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

# FIX: same absolute-path logic as main.py - both processes now always agree
# on exactly one camera_config.json location, regardless of folder structure
# or which directory you launch each script from.
NETRA_HOME = os.environ.get("NETRA_HOME", os.path.join(os.path.expanduser("~"), ".netra"))
os.makedirs(NETRA_HOME, exist_ok=True)
CONFIG_PATH = os.environ.get("NETRA_CONFIG_PATH", os.path.join(NETRA_HOME, "camera_config.json"))
BACKEND_API_URL = "http://127.0.0.1:8000/api/ai-stream"
print(f"[NETRA ENGINE] camera_config.json path -> {CONFIG_PATH}")

# --- TUNABLE CONSTANTS (sab yahin se control hote hain) ---
PERSON_CONF_THRESH = 0.5      # FIX: pehle YOLO ka default 0.25 use ho raha tha -> empty room me
                               # shadows/noise bhi "person" ban jaate the. 0.5 = zyada confident hone
                               # par hi count hoga -> khaali camera par ab reliably 0 aayega.
PERSON_IOU_THRESH = 0.45
MIN_BOX_AREA_RATIO = 0.01     # bahut chhote/spurious boxes (frame area ka 1% se kam) ko ignore karo

KPT_CONF_THRESH = 0.30        # FIX: pehle 0.35 tha jo backlit/low-light me wrist ko miss kar raha tha
DRAW_KPT_CONF_THRESH = 0.30   # skeleton dots draw karne ke liye minimum confidence

REQUIRED_HOLD_TIME = 3.0      # itne second haath upar rehna chahiye SOS confirm hone ke liye
GESTURE_COOLDOWN = 1.2        # itne second tak gesture "miss" hone par bhi timer pause rahega (flicker-proof)
ALERT_COOLDOWN_SEC = 3.0      # backend ko har kitne second me status bhejna hai

# FIX: pehle model 640px par chalta tha, jiske wajah se CPU par ek frame ~400-700ms
# le sakta tha. 320px par accuracy me mamuli farak padta hai (khaaskar close-range
# selfie-style testing me) lekin speed roughly 2-3x badh jaati hai.
INFERENCE_IMG_SIZE = 320

print("[NETRA ENGINE] Initializing YOLOv8-Pose on CPU...")
try:
    pose_model = YOLO("yolov8n-pose.pt")
    pose_model.to("cpu")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit()

output_frame = None       # AI-processed frame (boxes/skeleton/banner) -> served at /live-feed
raw_output_frame = None   # untouched camera frame, no overlay          -> served at /live-feed-raw
lock = threading.Lock()


class FreshFrameReader:
    """
    FIX (root cause of the ~1 min lag): cv2.VideoCapture() by default buffers
    frames from a network/IP camera stream in the order they arrive. If our
    CPU-bound YOLO inference can't keep up with the phone's frame rate, that
    buffer just keeps growing - cap.read() always hands us the OLDEST queued
    frame, not the newest. The delay between "what the phone sees right now"
    and "what we're looking at" grows continuously the longer the app runs,
    which is exactly the drifting ~1 minute lag you saw.

    Fix: read the camera continuously in its own background thread as fast as
    the network allows, and always overwrite a single shared "latest frame"
    slot. The main processing loop never blocks on the network and always
    grabs whatever is freshest - if inference is slow, frames are simply
    skipped instead of queued, so the feed always stays close to real-time.
    """

    def __init__(self, url):
        self.url = url
        self.cap = cv2.VideoCapture(url)
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
                time.sleep(0.2)  # camera down - don't spin-loop hot

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
def get_camera_url():
    """
    FIX: main.py writes both 'CAMERA_1_URL' and legacy 'cam_1' keys now, but we still
    check every known key name here defensively, in that priority order, so a stale
    config file (or a future frontend change) never silently falls back to device 0
    the way it did before (that was the root cause of the engine not seeing the real
    DroidCam feed at all).
    """
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            for key in ("CAMERA_1_URL", "cam_1", "camera_1_url"):
                if key in config and config[key]:
                    url = config[key]
                    return int(url) if str(url).isdigit() else url
        except Exception:
            pass
    return 0

def send_status_to_backend(persons, sos_active, camera_online=True):
    payload = {
        "camera_id": "Netra_Frontend_Stream",
        "threat_level": "CRITICAL" if sos_active else ("OFFLINE" if not camera_online else "NORMAL"),
        "persons_detected": persons,
        "sos_active": sos_active,
        "location_name": "Dynamic Dashboard Camera",
        "frame_timestamp": datetime.now().isoformat()
    }
    try:
        requests.post(BACKEND_API_URL, json=payload, timeout=1)
    except Exception:
        pass

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
    global output_frame, raw_output_frame, lock

    current_url = get_camera_url()
    print(f"[NETRA ENGINE] Opening camera source -> {current_url!r}"
          f"{'  (falling back to local webcam device 0 - no valid URL found in config)' if current_url == 0 else ''}")
    reader = FreshFrameReader(current_url)

    last_alert_time = 0
    sos_start_time = None
    last_gesture_time = 0
    fps_log_time = 0
    frame_count_since_log = 0

    while True:
        new_url = get_camera_url()
        if new_url != current_url:
            print(f"[NETRA ENGINE] Camera source changed -> {new_url!r} (was {current_url!r})")
            reader.release()
            current_url = new_url
            reader = FreshFrameReader(current_url)
            time.sleep(1)

        success, frame = reader.read()
        current_time = time.time()

        # FIX: simple rolling FPS counter printed every ~5s, so you can see in
        # the terminal that processing speed is healthy (aim: several FPS on
        # CPU with imgsz=320, not the sub-1-FPS that caused the old lag).
        frame_count_since_log += 1
        if current_time - fps_log_time > 5:
            if fps_log_time != 0:
                fps = frame_count_since_log / (current_time - fps_log_time)
                print(f"[NETRA ENGINE] Processing ~{fps:.1f} FPS")
            fps_log_time = current_time
            frame_count_since_log = 0

        if not success:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "CAMERA OFFLINE OR LOADING...", (50, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # FIX: pehle camera down hone par backend ko kabhi update hi nahi milta tha,
            # so frontend purana (stale) count/SOS state dikhata rehta tha. Ab reset+report karo.
            sos_start_time = None
            if (current_time - last_alert_time > ALERT_COOLDOWN_SEC):
                threading.Thread(target=send_status_to_backend, args=(0, False, False), daemon=True).start()
                last_alert_time = current_time

            with lock:
                raw_output_frame = frame.copy()

            time.sleep(0.5)
        else:
            frame = cv2.resize(frame, (640, 480))

            # FIX: publish the untouched camera frame here, BEFORE any boxes/
            # skeleton/banner get drawn on `frame` below. This is what makes
            # /live-feed-raw an actual "live camera" feed instead of showing
            # nothing - previously there was no raw frame captured anywhere,
            # only the fully-processed one, so a frontend tile bound to a raw
            # feed had no endpoint to pull from.
            with lock:
                raw_output_frame = frame.copy()

            frame_area = frame.shape[0] * frame.shape[1]

            # FIX: explicit conf/iou so low-confidence "ghost" detections don't count
            # as persons, AND imgsz=320 (was implicitly 640) roughly doubles/triples
            # CPU throughput - this is the other half of the lag fix, alongside
            # FreshFrameReader above.
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
                        draw_skeleton(frame, kpts)  # FIX: this call was completely missing before

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
                        sos_start_time = None  # haath sach me neeche gaya hai, reset karo
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

        with lock:
            output_frame = frame.copy()

# ==========================================
# 3. VIDEO STREAMING ENDPOINT (MJPEG)
# ==========================================
def generate_mjpeg_stream():
    global output_frame, lock
    while True:
        with lock:
            if output_frame is None:
                continue
            flag, encoded_image = cv2.imencode(".jpg", output_frame)
            if not flag:
                continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

        time.sleep(0.05)

@app.get("/live-feed")
def video_feed():
    return StreamingResponse(generate_mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")


def generate_raw_mjpeg_stream():
    """Same idea as generate_mjpeg_stream(), but reads raw_output_frame
    (no boxes/skeleton/banner) instead of the AI-processed one."""
    global raw_output_frame, lock
    while True:
        with lock:
            if raw_output_frame is None:
                continue
            flag, encoded_image = cv2.imencode(".jpg", raw_output_frame)
            if not flag:
                continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

        time.sleep(0.05)

# FIX: this is the missing "live camera" feed. /live-feed only ever sent the
# AI-processed frame (boxes/skeleton/PERSONS banner burned in) - there was no
# endpoint anywhere serving the plain camera image, which is why the
# frontend's raw "live camera" tile never had anything to point at even
# though the AI-processed tile worked fine. Point that <img>/<video> src at
# http://<engine-host>:8001/live-feed-raw
@app.get("/live-feed-raw")
def raw_video_feed():
    return StreamingResponse(generate_raw_mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")


# ==========================================
# 4. SERVER STARTUP
# ==========================================
if __name__ == "__main__":
    ai_thread = threading.Thread(target=ai_processing_loop, daemon=True)
    ai_thread.start()

    print("\n🚀 [NETRA UNIFIED] AI Engine Running (CPU Mode + Anti-Flicker 3-Sec Logic)!")
    print("📺 Live Feed URL: http://127.0.0.1:8001/live-feed\n")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")