import cv2
import time
import os
import json
import numpy as np
import threading
import requests
from datetime import datetime
from ultralytics import YOLO
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

# ==========================================
# 0. SERVER & CONFIGURATION
# ==========================================
app = FastAPI()

# WEBCAM-ONLY MODE: DroidCam / camera_config.json is no longer used at all.
# The engine always opens the local webcam directly. Override the device
# index with the NETRA_WEBCAM_INDEX env var if 0 isn't your camera
# (e.g. NETRA_WEBCAM_INDEX=1 on machines with a built-in cam + USB cam).
WEBCAM_INDEX = int(os.environ.get("NETRA_WEBCAM_INDEX", "0"))
BACKEND_API_URL = "http://127.0.0.1:8000/api/ai-stream"
print(f"[NETRA ENGINE] Webcam-only mode -> device index {WEBCAM_INDEX}")

# --- TUNABLE CONSTANTS ---
PERSON_CONF_THRESH = 0.5      # min confidence for a YOLO box to count as "person"
PERSON_IOU_THRESH = 0.45
MIN_BOX_AREA_RATIO = 0.01     # ignore boxes smaller than 1% of frame area (noise)

KPT_CONF_THRESH = 0.30        # keypoint confidence threshold for pose
DRAW_KPT_CONF_THRESH = 0.30   # min confidence to draw a skeleton dot

REQUIRED_HOLD_TIME = 3.0      # seconds hand must stay up for SOS to confirm
GESTURE_COOLDOWN = 2.0        # seconds gesture can "flicker off" without resetting hold timer
                               # (kept generous so a brief FPS dip doesn't reset a real SOS attempt)
ALERT_COOLDOWN_SEC = 3.0      # how often we push status to backend

INFERENCE_IMG_SIZE = 320      # good CPU speed/accuracy balance for a laptop webcam
JPEG_QUALITY = 80              # lower = faster encode, frees up CPU for the YOLO thread

print("[NETRA ENGINE] Initializing YOLOv8-Pose on CPU...")
try:
    pose_model = YOLO("yolov8n-pose.pt")
    pose_model.to("cpu")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit()

output_frame = None       # AI-processed frame (boxes/skeleton/banner) -> served at /live-feed
raw_output_frame = None   # untouched camera frame, no overlay          -> served at /live-feed-raw

# FIX: these used to share ONE lock. Every /live-feed and /live-feed-raw
# client held that same lock while running cv2.imencode() (not instant),
# which repeatedly blocked the CPU-heavy AI thread from writing its next
# frame - the more browser tabs/connections open, the worse the YOLO loop
# slowed down (and a slow loop is exactly what breaks the SOS hold timer,
# since it's wall-clock based - see GESTURE_COOLDOWN below). Separate locks
# mean streaming a JPEG never blocks the AI thread's own frame handoff.
output_lock = threading.Lock()
raw_lock = threading.Lock()


class WebcamFrameReader:
    """
    Reads the local webcam continuously in a background thread and always
    exposes the single freshest frame. The main loop never blocks waiting
    on the camera and never falls behind (same anti-lag design as before,
    just pointed at a local device instead of a network camera).
    """

    def __init__(self, device_id=0):
        self.device_id = device_id
        self.cap = cv2.VideoCapture(device_id)
        if not self.cap.isOpened():
            print(f"[NETRA ENGINE] ERROR: could not open webcam device {device_id}. "
                  f"Is another app using the camera, or is the index wrong?")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.lock = threading.Lock()
        self.frame = None
        self.success = False
        self.running = True
        self.thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.thread.start()

    def _reader_loop(self):
        while self.running:
            ok, frame = self.cap.read()
            with self.lock:
                self.success = ok
                if ok:
                    self.frame = frame
            if not ok:
                time.sleep(0.2)  # camera not ready / disconnected - don't spin-loop hot

    def read(self):
        with self.lock:
            if self.frame is None:
                return self.success, None
            return self.success, self.frame.copy()

    def release(self):
        self.running = False
        self.thread.join(timeout=1.0)
        self.cap.release()


# COCO-17 keypoint skeleton connections (for drawing dots + bones)
SKELETON = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),          # shoulders/arms
    (5, 11), (6, 12), (11, 12),                        # torso
    (11, 13), (13, 15), (12, 14), (14, 16),            # legs
    (0, 5), (0, 6),                                     # neck-ish
    (0, 1), (0, 2), (1, 3), (2, 4),                     # face
]

# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================
def send_status_to_backend(persons, sos_active, camera_online=True):
    payload = {
        "camera_id": "Netra_Webcam",
        "threat_level": "CRITICAL" if sos_active else ("OFFLINE" if not camera_online else "NORMAL"),
        "persons_detected": persons,
        "sos_active": sos_active,
        "location_name": "Local Webcam",
        "frame_timestamp": datetime.now().isoformat()
    }
    try:
        requests.post(BACKEND_API_URL, json=payload, timeout=1)
    except Exception:
        pass  # backend may be offline - don't block the video loop for this

def draw_skeleton(frame, kpts):
    """Draw joint dots + connecting bones for one person's keypoints."""
    pts = {}
    for idx, (x, y, c) in enumerate(kpts):
        if c > DRAW_KPT_CONF_THRESH:
            pt = (int(x), int(y))
            pts[idx] = pt
            cv2.circle(frame, pt, 4, (0, 220, 255), -1)
    for a, b in SKELETON:
        if a in pts and b in pts:
            cv2.line(frame, pts[a], pts[b], (0, 220, 255), 2)

# ==========================================
# 2. CORE AI PROCESSING THREAD
# ==========================================
def ai_processing_loop():
    global output_frame, raw_output_frame, output_lock, raw_lock

    reader = WebcamFrameReader(WEBCAM_INDEX)

    last_alert_time = 0
    sos_start_time = None
    last_gesture_time = 0
    fps_log_time = 0
    frame_count_since_log = 0

    while True:
        try:
            success, frame = reader.read()
            current_time = time.time()

            # simple rolling FPS counter, printed every ~5s
            frame_count_since_log += 1
            if current_time - fps_log_time > 5:
                if fps_log_time != 0:
                    fps = frame_count_since_log / (current_time - fps_log_time)
                    print(f"[NETRA ENGINE] Processing ~{fps:.1f} FPS")
                fps_log_time = current_time
                frame_count_since_log = 0

            if not success:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "WEBCAM OFFLINE OR LOADING...", (50, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                sos_start_time = None
                if (current_time - last_alert_time > ALERT_COOLDOWN_SEC):
                    threading.Thread(target=send_status_to_backend, args=(0, False, False), daemon=True).start()
                    last_alert_time = current_time

                with raw_lock:
                    raw_output_frame = frame.copy()

                time.sleep(0.5)
            else:
                frame = cv2.resize(frame, (640, 480))

                # untouched frame, published BEFORE any boxes/skeleton get drawn
                with raw_lock:
                    raw_output_frame = frame.copy()

                frame_area = frame.shape[0] * frame.shape[1]

                results = pose_model(frame, verbose=False, device="cpu",
                                      conf=PERSON_CONF_THRESH, iou=PERSON_IOU_THRESH,
                                      imgsz=INFERENCE_IMG_SIZE)

                count = 0
                gesture_in_current_frame = False

                for r in results:
                    boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else []
                    keypoints = r.keypoints.data.cpu().numpy() if r.keypoints is not None else []

                    for i, box in enumerate(boxes):
                        x1, y1, x2, y2 = map(int, box[:4])
                        box_area = max(0, x2 - x1) * max(0, y2 - y1)
                        if box_area < MIN_BOX_AREA_RATIO * frame_area:
                            continue  # too tiny to be a real person -> noise, skip

                        count += 1
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        if len(keypoints) > i and len(keypoints[i]) >= 11:
                            kpts = keypoints[i]
                            draw_skeleton(frame, kpts)

                            l_sh_y, l_sh_conf = kpts[5][1], kpts[5][2]
                            r_sh_y, r_sh_conf = kpts[6][1], kpts[6][2]
                            l_wr_y, l_wr_conf = kpts[9][1], kpts[9][2]
                            r_wr_y, r_wr_conf = kpts[10][1], kpts[10][2]

                            left_raised = (l_wr_conf > KPT_CONF_THRESH and l_sh_conf > KPT_CONF_THRESH and l_wr_y < l_sh_y)
                            right_raised = (r_wr_conf > KPT_CONF_THRESH and r_sh_conf > KPT_CONF_THRESH and r_wr_y < r_sh_y)

                            if left_raised or right_raised:
                                gesture_in_current_frame = True

                # --- ANTI-FLICKER HOLD LOGIC ---
                sos_triggered = False

                if gesture_in_current_frame:
                    last_gesture_time = current_time
                    if sos_start_time is None:
                        sos_start_time = current_time

                    hold_duration = current_time - sos_start_time

                    if hold_duration >= REQUIRED_HOLD_TIME:
                        sos_triggered = True
                        cv2.putText(frame, "SOS CONFIRMED!", (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        cv2.putText(frame, f"HOLD GESTURE: {hold_duration:.1f}s / {REQUIRED_HOLD_TIME}s",
                                    (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                else:
                    if sos_start_time is not None:
                        time_since_last_seen = current_time - last_gesture_time
                        if time_since_last_seen > GESTURE_COOLDOWN:
                            sos_start_time = None  # hand genuinely went down, reset
                        else:
                            hold_duration = last_gesture_time - sos_start_time
                            cv2.putText(frame, f"HOLD GESTURE: {hold_duration:.1f}s ...",
                                        (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                # Draw Status Banner
                banner_color = (0, 0, 255) if sos_triggered else (0, 255, 0)
                cv2.putText(frame, f"PERSONS: {count} | SOS: {'ACTIVE' if sos_triggered else 'NORMAL'}",
                            (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, banner_color, 2)

                # Send Backend Alert
                if (current_time - last_alert_time > ALERT_COOLDOWN_SEC) or sos_triggered:
                    threading.Thread(target=send_status_to_backend, args=(count, sos_triggered, True), daemon=True).start()
                    last_alert_time = current_time

                with output_lock:
                    output_frame = frame.copy()
        except Exception as e:
            print(f"[NETRA ENGINE] Error in processing loop (frame skipped): {e}", flush=True)
            time.sleep(0.05)

# ==========================================
# 3. VIDEO STREAMING ENDPOINTS (MJPEG)
# ==========================================
def generate_mjpeg_stream():
    global output_frame, output_lock
    while True:
        with output_lock:
            frame_to_send = None if output_frame is None else output_frame.copy()

        if frame_to_send is None:
            time.sleep(0.01)
            continue

        flag, encoded_image = cv2.imencode(".jpg", frame_to_send, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if not flag:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

        time.sleep(0.05)

@app.get("/live-feed")
def video_feed():
    return StreamingResponse(generate_mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")


def generate_raw_mjpeg_stream():
    """Same as generate_mjpeg_stream(), but streams raw_output_frame
    (plain webcam image, no boxes/skeleton/banner)."""
    global raw_output_frame, raw_lock
    while True:
        with raw_lock:
            frame_to_send = None if raw_output_frame is None else raw_output_frame.copy()

        if frame_to_send is None:
            time.sleep(0.01)
            continue

        flag, encoded_image = cv2.imencode(".jpg", frame_to_send, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if not flag:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

        time.sleep(0.05)

@app.get("/live-feed-raw")
def raw_video_feed():
    return StreamingResponse(generate_raw_mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")


# ==========================================
# 4. SERVER STARTUP
# ==========================================
if __name__ == "__main__":
    ai_thread = threading.Thread(target=ai_processing_loop, daemon=True)
    ai_thread.start()

    print("\n🚀 [NETRA UNIFIED] AI Engine Running (Webcam Mode + Anti-Flicker 3-Sec Logic)!")
    print("📺 Processed Feed: http://127.0.0.1:8001/live-feed")
    print("📺 Raw Feed:       http://127.0.0.1:8001/live-feed-raw\n")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")