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
import base64
import tempfile
from google import genai
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY")) if os.environ.get("GEMINI_API_KEY") else None
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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

# ==========================================
# 1. GOOGLE VISION & DRIVE SETUP
# ==========================================
# Initialize Google Vision API (using google-genai) - client already created above
if client:
    print("[NETRA ENGINE] Google Vision API (Gemini) initialized.")
else:
    print("[NETRA ENGINE] WARNING: GEMINI_API_KEY not set. Vision API disabled.")

# Google Drive setup
DRIVE_CREDS_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
DRIVE_AVAILABLE = False
drive_service = None
try:
    if os.path.exists(DRIVE_CREDS_FILE):
        credentials = service_account.Credentials.from_service_account_file(
            DRIVE_CREDS_FILE, scopes=DRIVE_SCOPES)
        drive_service = build("drive", "v3", credentials=credentials)
        DRIVE_AVAILABLE = True
        print("[NETRA ENGINE] Google Drive API initialized.")
    else:
        print(f"[NETRA ENGINE] WARNING: Google Drive credentials not found at {DRIVE_CREDS_FILE}. Drive upload disabled.")
except Exception as e:
    print(f"[NETRA ENGINE] WARNING: Failed to initialize Google Drive: {e}. Drive upload disabled.")

# ==========================================
# 2. FRAME BUFFERS & LOCKS
# ==========================================
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

latest_forensic_report = None

# ==========================================
# 3. WEBCAM FRAME READER
# ==========================================
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

# ==========================================
# 4. HELPER FUNCTIONS
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
# 5. GOOGLE VISION & DRIVE FUNCTIONS
# ==========================================
def capture_and_save_frame(frame, prefix="sos"):
    """Capture a frame and save it to a temporary file, return the file path."""
    try:
        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(temp_dir, filename)

        # Save the frame as JPEG
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        return filepath
    except Exception as e:
        print(f"[NETRA ENGINE] Failed to capture frame: {e}")
        return None

def generate_forensic_report(image_path):
    """Use Google Vision API (Gemini) to generate a forensic incident report from an image."""
    if not client or not image_path or not os.path.exists(image_path):
        return None

    try:
        # Upload the image to Gemini
        uploaded_file = client.upload_file(path=image_path)

        # Prompt for forensic report
        prompt = "Analyze this surveillance emergency snapshot. Generate a structured forensic incident report including threat level, description of the situation, and timestamp."

        # Generate content
        response = client.generate_content(
            model="gemini-1.5-flash",  # or another vision model
            contents=[prompt, uploaded_file]
        )

        # Try to parse the response as JSON
        report_text = response.text
        # Clean the response to extract JSON
        # Remove any markdown code block markers if present
        if "```json" in report_text:
            report_text = report_text.split("```json")[1].split("```")[0]
        elif "```" in report_text:
            report_text = report_text.split("```")[1].split("```")[0]

        report = json.loads(report_text.strip())

        # Ensure required fields exist
        if "threat_level" not in report:
            report["threat_level"] = "UNKNOWN"
        if "description" not in report:
            report["description"] = "No description provided."
        if "timestamp" not in report:
            report["timestamp"] = datetime.now().isoformat()

        return report
    except Exception as e:
        print(f"[NETRA ENGINE] Failed to generate forensic report: {e}")
        return None

def upload_to_drive(image_path, report_dict):
    """Upload the captured image and forensic report to Google Drive."""
    if not DRIVE_AVAILABLE or not drive_service or not image_path or not os.path.exists(image_path):
        return None, None

    try:
        # Upload the image
        image_filename = os.path.basename(image_path)
        image_file_metadata = {"name": f"Netra_SOS_{image_filename}"}
        image_media = MediaFileUpload(image_path, mimetype="image/jpeg", resumable=True)
        image_uploaded = drive_service.files().create(
            body=image_file_metadata,
            media_body=image_media,
            fields="id, webViewLink"
        ).execute()

        # Make the image publicly readable
        drive_service.permissions().create(
            fileId=image_uploaded.get("id"),
            body={"type": "anyone", "role": "reader"}
        ).execute()
        image_link = image_uploaded.get("webViewLink")

        # Create a temporary file for the report
        report_temp = None
        report_link = None
        try:
            report_temp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(report_dict, report_temp, indent=2)
            report_temp.close()

            # Upload the report
            report_filename = f"report_{os.path.splitext(image_filename)[0]}.json"
            report_file_metadata = {"name": f"Netra_SOS_Report_{report_filename}"}
            report_media = MediaFileUpload(report_temp.name, mimetype="application/json", resumable=True)
            report_uploaded = drive_service.files().create(
                body=report_file_metadata,
                media_body=report_media,
                fields="id, webViewLink"
            ).execute()

            # Make the report publicly readable
            drive_service.permissions().create(
                fileId=report_uploaded.get("id"),
                body={"type": "anyone", "role": "reader"}
            ).execute()
            report_link = report_uploaded.get("webViewLink")
        finally:
            # Clean up the temporary report file
            if report_temp and os.path.exists(report_temp.name):
                os.unlink(report_temp.name)

        return image_link, report_link
    except Exception as e:
        print(f"[NETRA ENGINE] Failed to upload to Google Drive: {e}")
        return None, None

def process_sos_confirmation(raw_frame):
    """Handle SOS confirmation: capture frame, generate report, upload to Drive."""
    # Save raw frame as fixed name for SOS incident
    temp_dir = tempfile.gettempdir()
    frame_path = os.path.join(temp_dir, "sos_incident_snapshot.jpg")
    try:
        cv2.imwrite(frame_path, raw_frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    except Exception as e:
        print(f"[NETRA ENGINE] Failed to capture frame: {e}")
        return

    # Generate forensic report
    report = generate_forensic_report(frame_path)
    if not report:
        print("[NETRA ENGINE] SOS confirmation: Failed to generate forensic report.")
        # Still upload the image even if report fails?
        # We'll upload the image with a placeholder report
        report = {
            "threat_level": "UNKNOWN",
            "description": "Failed to generate report via Gemini Vision.",
            "timestamp": datetime.now().isoformat()
        }

    global latest_forensic_report
    latest_forensic_report = report

    # Upload to Drive
    image_link, report_link = upload_to_drive(frame_path, report)
    if image_link:
        print(f"[NETRA ENGINE] SOS confirmation: Image uploaded to Drive: {image_link}")
    else:
        print("[NETRA ENGINE] SOS confirmation: Failed to upload image to Drive.")

    if report_link:
        print(f"[NETRA ENGINE] SOS confirmation: Report uploaded to Drive: {report_link}")
    else:
        print("[NETRA ENGINE] SOS confirmation: Failed to upload report to Drive.")

    # Clean up the temporary frame file
    try:
        if frame_path and os.path.exists(frame_path):
            os.unlink(frame_path)
    except Exception as e:
        print(f"[NETRA ENGINE] Failed to delete temporary frame file: {e}")

# ==========================================
# 6. COCO-17 KEYPOINT SKELETON
# ==========================================
SKELETON = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),          # shoulders/arms
    (5, 11), (6, 12), (11, 12),                        # torso
    (11, 13), (13, 15), (12, 14), (14, 16),            # legs
    (0, 5), (0, 6),                                     # neck-ish
    (0, 1), (0, 2), (1, 3), (2, 4),                     # face
]

# ==========================================
# 7. CORE AI PROCESSING THREAD
# ==========================================
def ai_processing_loop():
    global output_frame, raw_output_frame, output_lock, raw_lock

    reader = WebcamFrameReader(WEBCAM_INDEX)

    last_alert_time = 0
    sos_start_time = None
    last_gesture_time = 0
    fps_log_time = 0
    frame_count_since_log = 0
    last_sos_processed_time = 0  # To avoid processing the same SOS event multiple times
    SOS_PROCESS_COOLDOWN = 10.0  # Seconds to wait before processing another SOS event

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

                # Send Backend Alert (for frontend updates)
                if (current_time - last_alert_time > ALERT_COOLDOWN_SEC) or sos_triggered:
                    threading.Thread(target=send_status_to_backend, args=(count, sos_triggered, True), daemon=True).start()
                    last_alert_time = current_time

                # Process SOS confirmation for forensic report and Drive upload
                if sos_triggered and (current_time - last_sos_processed_time > SOS_PROCESS_COOLDOWN):
                    # Process in a separate thread to avoid blocking the video loop
                    threading.Thread(target=process_sos_confirmation, args=(frame.copy()), daemon=True).start()
                    last_sos_processed_time = current_time

                with output_lock:
                    output_frame = frame.copy()
        except Exception as e:
            print(f"[NETRA ENGINE] Error in processing loop (frame skipped): {e}", flush=True)
            time.sleep(0.05)

# ==========================================
# 8. VIDEO STREAMING ENDPOINTS (MJPEG)
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

@app.post("/set-gemini-key")
async def set_gemini_key(payload: dict):
    global client
    api_key = payload.get("api_key")
    if api_key:
        client = genai.Client(api_key=api_key)
        print("[NETRA ENGINE] Gemini API key updated via endpoint.")
        return {"status": "success"}
    else:
        return {"status": "error", "message": "API key missing"}, 400

@app.get("/latest-forensic-report")
async def get_latest_forensic_report():
    global latest_forensic_report
    if latest_forensic_report:
        return latest_forensic_report
    else:
        return {"status": "no report yet"}


# ==========================================
# 9. SERVER STARTUP
# ==========================================
if __name__ == "__main__":
    ai_thread = threading.Thread(target=ai_processing_loop, daemon=True)
    ai_thread.start()

    print("\n🚀 [NETRA UNIFIED] AI Engine Running (Webcam Mode + Anti-Flicker 3-Sec Logic)!")
    print("📺 Processed Feed: http://127.0.0.1:8001/live-feed")
    print("📺 Raw Feed:       http://127.0.0.1:8001/live-feed-raw\n")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")