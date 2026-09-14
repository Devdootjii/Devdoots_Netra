"""
NETRA UNIFIED ENGINE  —  the single core that does everything:
camera capture -> YOLOv8-pose person + SOS gesture detection ->
backend alerting -> Gemini Vision forensic report -> Google Drive evidence archive.

Runs a FastAPI server on port 8001 serving two MJPEG streams:
    /live-feed        AI-processed frame (boxes / skeleton / status banner)
    /live-feed-raw    untouched camera frame (for a plain "live camera" tile)

Run from the repo root:   python engine/netra_engine.py
"""

import base64
import json
import os
import threading
import time
from datetime import datetime

import cv2
import numpy as np
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from ultralytics import YOLO

from gemini_helper import get_client, generate_with_image


# ===========================================================================
# 0. CONFIGURATION  (everything tunable lives here)
# ===========================================================================
# Load .env from repo root (one level up from engine/)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

app = FastAPI(title="NETRA Engine")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Single source of truth for camera config.
NETRA_HOME = os.environ.get("NETRA_HOME", os.path.join(REPO_ROOT, ".runtime"))
os.makedirs(NETRA_HOME, exist_ok=True)
CONFIG_PATH = os.environ.get(
    "NETRA_CONFIG_PATH", os.path.join(NETRA_HOME, "camera_config.json")
)

BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8000/api/ai-stream")

# Model weights: prefer the pose model bundled in the repo, allow override.
DEFAULT_MODEL = os.path.join(REPO_ROOT, "models", "yolov8n-pose.pt")
MODEL_PATH = os.environ.get("NETRA_MODEL_PATH", DEFAULT_MODEL)

# --- Cloud / AI keys (optional; engine still runs if these are absent) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DRIVE_CREDS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")  # optional: upload into a folder

# --- Detection tunables ---
PERSON_CONF_THRESH = 0.5      # was 0.25 -> empty-room noise counted as persons
PERSON_IOU_THRESH = 0.45
MIN_BOX_AREA_RATIO = 0.01     # ignore boxes < 1% of frame area

KPT_CONF_THRESH = 0.30        # wrist/shoulder confidence gate
DRAW_KPT_CONF_THRESH = 0.30

REQUIRED_HOLD_TIME = 3.0      # seconds hand must stay up to confirm SOS
GESTURE_COOLDOWN = 1.2        # flicker-proof grace while hand briefly drops
ALERT_COOLDOWN_SEC = 3.0      # how often backend gets a status update
SOS_REPORT_COOLDOWN = 15.0    # min gap between two Gemini/Drive evidence packs
INFERENCE_IMG_SIZE = 320      # 640->320 roughly 2-3x CPU throughput

print(f"[NETRA ENGINE] config path   -> {CONFIG_PATH}")
print(f"[NETRA ENGINE] backend URL    -> {BACKEND_API_URL}")
print(f"[NETRA ENGINE] model path     -> {MODEL_PATH}")
print(f"[NETRA ENGINE] gemini         -> {'ON' if GEMINI_API_KEY else 'OFF (set GEMINI_API_KEY to enable forensic reports)'}")
print(f"[NETRA ENGINE] drive archive  -> {'ON' if DRIVE_CREDS else 'OFF (set GOOGLE_APPLICATION_CREDENTIALS to enable evidence upload)'}")
if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("AIzaSy"):
    print("[NETRA ENGINE] ⚠️  GEMINI_API_KEY doesn't look like a valid Gemini API key "
          "(valid keys start with 'AIzaSy'). Get one from https://aistudio.google.com/apikey")

# Default camera config for the webcam-first demo. Written once if missing.
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"cam_1": "0", "cam_2": ""}, f, indent=4)

print("[NETRA ENGINE] Initializing YOLOv8-Pose (CPU)...")
try:
    pose_model = YOLO(MODEL_PATH)
    pose_model.to("cpu")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    raise SystemExit(1)

output_frame = None        # AI-processed frame  -> /live-feed
raw_output_frame = None    # untouched camera frame -> /live-feed-raw
lock = threading.Lock()


# ===========================================================================
# 1. CAMERA READER  (kills the drifting ~1 min lag)
# ===========================================================================
class FreshFrameReader:
    """Background thread that always keeps the newest frame; old frames are
    dropped instead of buffered. The main loop never blocks on the network."""

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
                time.sleep(0.2)

    def read(self):
        with self.lock:
            if self.frame is None:
                return self.success, None
            return self.success, self.frame.copy()

    def release(self):
        self.running = False
        self.thread.join(timeout=1.0)
        self.cap.release()


# COCO-17 skeleton connections for drawing.
SKELETON = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),       # shoulders/arms
    (5, 11), (6, 12), (11, 12),                      # torso
    (11, 13), (13, 15), (12, 14), (14, 16),          # legs
    (0, 5), (0, 6),                                   # neck-ish
    (0, 1), (0, 2), (1, 3), (2, 4),                   # face
]


# ===========================================================================
# 2. HELPERS
# ===========================================================================
def get_camera_url():
    """Read camera source from config. Accepts known key names. An integer
    string (e.g. "0") is treated as a local webcam device index. Falls back
    to the laptop webcam (device 0) for the demo flow."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            for key in ("CAMERA_1_URL", "cam_1", "camera_1_url"):
                if key in config and config[key] not in (None, ""):
                    url = config[key]
                    return int(url) if str(url).strip().isdigit() else url
        except Exception:
            pass
    return 0  # laptop webcam


def encode_frame_b64(frame):
    try:
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return base64.b64encode(buf).decode("utf-8") if ok else None
    except Exception:
        return None


def send_status_to_backend(persons, sos_active, camera_online=True, snapshot_b64=None):
    payload = {
        "camera_id": "Netra_Frontend_Stream",
        "threat_level": "CRITICAL" if sos_active else ("OFFLINE" if not camera_online else "NORMAL"),
        "persons_detected": persons,
        "sos_active": sos_active,
        "location_name": "Dynamic Dashboard Camera",
        "frame_timestamp": datetime.now().isoformat(),
    }
    if snapshot_b64:
        payload["snapshot_b64"] = snapshot_b64
    try:
        requests.post(BACKEND_API_URL, json=payload, timeout=3)
    except Exception:
        pass


def draw_skeleton(frame, kpts):
    pts = {}
    for idx, (x, y, c) in enumerate(kpts):
        if c > DRAW_KPT_CONF_THRESH:
            pt = (int(x), int(y))
            pts[idx] = pt
            cv2.circle(frame, pt, 4, (0, 220, 255), -1)
    for a, b in SKELETON:
        if a in pts and b in pts:
            cv2.line(frame, pts[a], pts[b], (0, 220, 255), 2)


# ---------------------------------------------------------------------------
# Gemini Vision forensic report + Google Drive evidence upload
# (run in a background thread so the camera loop never stalls)
# ---------------------------------------------------------------------------
def _generate_gemini_report(frame_b64):
    """Send the SOS snapshot to Gemini Vision and get back a structured
    forensic incident report. Returns the report text or None.

    FIX (Guide Fix 1): 'gemini-2.0-flash' is retired - hardcoding any single
    model name just breaks again next time Google renames/retires one.
    gemini_helper auto-discovers whichever flash model this API key can
    currently use, tries a few candidates, and remembers whichever works.
    """
    if not GEMINI_API_KEY:
        return None
    try:
        client = get_client(GEMINI_API_KEY)
        prompt = (
            "You are an emergency CCTV surveillance forensic engine. "
            "Analyze this captured frame and generate a concise structured "
            "incident report with these sections:\n"
            "1. Threat Level (High/Critical)\n"
            "2. Visual Description of the distress event\n"
            "3. Immediate Hazards\n"
            "4. Action Recommended\n"
            "5. Timestamp (use current UTC)."
        )
        image_bytes = base64.b64decode(frame_b64)
        text, model_used, error = generate_with_image(client, prompt, image_bytes)
        if error:
            print(f"[NETRA ENGINE] Gemini report failed: {error}")
            return None
        return text
    except Exception as e:
        print(f"[NETRA ENGINE] Gemini report failed: {e}")
        return None


def _save_evidence_locally(frame_bytes, report_text):
    """FIX (Guide Fix 2): Google has removed free Drive storage quota for
    service accounts, so _upload_to_drive() below now typically fails with
    403 'Service Accounts do not have storage quota'. Evidence should never
    be silently lost just because Drive is unavailable - this always saves
    the snapshot + report to a local 'sos_evidence/' folder first. Drive (if
    configured) is a bonus upload on top of this, never the only copy."""
    try:
        evidence_dir = os.path.join(REPO_ROOT, "sos_evidence")
        os.makedirs(evidence_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = os.path.join(evidence_dir, f"netra_sos_{ts}.jpg")
        report_path = os.path.join(evidence_dir, f"netra_sos_{ts}_report.txt")
        with open(img_path, "wb") as f:
            f.write(frame_bytes)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        return img_path, report_path
    except Exception as e:
        print(f"[NETRA ENGINE] Local evidence save failed: {e}")
        return None, None


def _upload_to_drive(frame_bytes, report_text):
    """Upload the SOS snapshot + Gemini report to Google Drive. Returns
    (image_link, report_link) or (None, None) if disabled/failed.

    NOTE (Guide Fix 2): this now commonly 403s because service accounts no
    longer get free Drive storage quota. That's fine - it's wrapped in
    try/except and _save_evidence_locally() above is the real evidence copy;
    this is best-effort only and must never break the engine."""
    if not DRIVE_CREDS or not os.path.exists(DRIVE_CREDS):
        return None, None
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaInMemoryUpload

        creds = service_account.Credentials.from_service_account_file(
            DRIVE_CREDS, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build("drive", "v3", credentials=creds)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        meta = {"name": f"netra_sos_{ts}.jpg"}
        if DRIVE_FOLDER_ID:
            meta["parents"] = [DRIVE_FOLDER_ID]
        img = service.files().create(
            body=meta,
            media_body=MediaInMemoryUpload(frame_bytes, mimetype="image/jpeg"),
            fields="id, webViewLink",
        ).execute()

        rmeta = {"name": f"netra_sos_{ts}_report.txt", "mimeType": "text/plain"}
        if DRIVE_FOLDER_ID:
            rmeta["parents"] = [DRIVE_FOLDER_ID]
        rep = service.files().create(
            body=rmeta,
            media_body=MediaInMemoryUpload(report_text.encode("utf-8"), mimetype="text/plain"),
            fields="id, webViewLink",
        ).execute()
        return img.get("webViewLink"), rep.get("webViewLink")
    except Exception as e:
        print(f"[NETRA ENGINE] Drive upload failed: {e}")
        return None, None


def run_sos_actions(frame):
    """Edge-triggered: build a forensic report from the SOS frame and archive
    it. Runs entirely in its own thread so the live loop is never blocked."""
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        return
    frame_bytes = buf.tobytes()
    frame_b64 = base64.b64encode(frame_bytes).decode("utf-8")

    report = _generate_gemini_report(frame_b64)
    if report is None:
        report = f"[{datetime.now().isoformat()}] SOS confirmed. Gemini reporting disabled or unavailable."

    # FIX (Guide Fix 2): save locally FIRST - this is now the guaranteed
    # evidence copy regardless of whether Drive quota works.
    local_img, local_report = _save_evidence_locally(frame_bytes, report)
    if local_img:
        print(f"[NETRA ENGINE] 💾 evidence saved locally -> {local_img}")

    img_link, rep_link = _upload_to_drive(frame_bytes, report)
    if img_link:
        print(f"[NETRA ENGINE] 🗂 evidence archived (Drive) -> {img_link}")
    if rep_link:
        print(f"[NETRA ENGINE] 📄 forensic report (Drive)  -> {rep_link}")
    print("[NETRA ENGINE] ---- Gemini Forensic Report ----\n" + report + "\n--------------------------------------")


# ===========================================================================
# 3. CORE AI PROCESSING THREAD
# ===========================================================================
def ai_processing_loop():
    global output_frame, raw_output_frame, lock

    current_url = get_camera_url()
    print(f"[NETRA ENGINE] Opening camera source -> {current_url!r}")
    reader = FreshFrameReader(current_url)

    last_alert_time = 0
    last_sos_action_time = 0          # throttle Gemini/Drive evidence packs
    sos_reported_for_current = False  # edge-trigger: fire once per SOS event
    sos_start_time = None
    last_gesture_time = 0
    fps_log_time = 0
    frame_count_since_log = 0

    while True:
        # Hot-swap camera source if the config changed (frontend can update it).
        new_url = get_camera_url()
        if new_url != current_url:
            print(f"[NETRA ENGINE] Camera source changed -> {new_url!r}")
            reader.release()
            current_url = new_url
            reader = FreshFrameReader(current_url)
            time.sleep(1)

        success, frame = reader.read()
        current_time = time.time()

        frame_count_since_log += 1
        if current_time - fps_log_time > 5:
            if fps_log_time != 0:
                fps = frame_count_since_log / (current_time - fps_log_time)
                print(f"[NETRA ENGINE] Processing ~{fps:.1f} FPS")
            fps_log_time = current_time
            frame_count_since_log = 0

        if not success:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "CAMERA OFFLINE OR LOADING...",
                        (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            sos_start_time = None
            sos_reported_for_current = False
            if current_time - last_alert_time > ALERT_COOLDOWN_SEC:
                threading.Thread(target=send_status_to_backend,
                                 args=(0, False, False), daemon=True).start()
                last_alert_time = current_time
            with lock:
                raw_output_frame = frame.copy()
            time.sleep(0.5)
        else:
            frame = cv2.resize(frame, (640, 480))
            with lock:
                raw_output_frame = frame.copy()

            frame_area = frame.shape[0] * frame.shape[1]
            results = pose_model(
                frame, verbose=False, device="cpu",
                conf=PERSON_CONF_THRESH, iou=PERSON_IOU_THRESH,
                imgsz=INFERENCE_IMG_SIZE,
            )

            count = 0
            gesture_in_current_frame = False

            for r in results:
                boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else []
                keypoints = r.keypoints.data.cpu().numpy() if r.keypoints is not None else []

                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = map(int, box[:4])
                    box_area = max(0, x2 - x1) * max(0, y2 - y1)
                    if box_area < MIN_BOX_AREA_RATIO * frame_area:
                        continue
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

            # --- anti-flicker hold logic ---
            sos_triggered = False
            if gesture_in_current_frame:
                last_gesture_time = current_time
                if sos_start_time is None:
                    sos_start_time = current_time
                hold_duration = current_time - sos_start_time
                if hold_duration >= REQUIRED_HOLD_TIME:
                    sos_triggered = True
                    cv2.putText(frame, "SOS CONFIRMED!", (15, 75),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, f"HOLD GESTURE: {hold_duration:.1f}s / {REQUIRED_HOLD_TIME}s",
                                (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            else:
                if sos_start_time is not None:
                    time_since_last_seen = current_time - last_gesture_time
                    if time_since_last_seen > GESTURE_COOLDOWN:
                        sos_start_time = None
                        sos_reported_for_current = False
                    else:
                        hold_duration = last_gesture_time - sos_start_time
                        cv2.putText(frame, f"HOLD GESTURE: {hold_duration:.1f}s ...",
                                    (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # --- status banner ---
            banner_color = (0, 0, 255) if sos_triggered else (0, 255, 0)
            cv2.putText(frame, f"PERSONS: {count} | SOS: {'ACTIVE' if sos_triggered else 'NORMAL'}",
                        (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, banner_color, 2)

            # --- backend alert (level-triggered, throttled) ---
            if (current_time - last_alert_time > ALERT_COOLDOWN_SEC) or sos_triggered:
                snapshot_b64 = encode_frame_b64(frame) if sos_triggered else None
                threading.Thread(
                    target=send_status_to_backend,
                    args=(count, sos_triggered, True, snapshot_b64),
                    daemon=True,
                ).start()
                last_alert_time = current_time

            # --- forensic report + Drive archive (edge-triggered, throttled) ---
            if sos_triggered and not sos_reported_for_current:
                if current_time - last_sos_action_time > SOS_REPORT_COOLDOWN:
                    threading.Thread(target=run_sos_actions, args=(frame.copy(),), daemon=True).start()
                    sos_reported_for_current = True
                    last_sos_action_time = current_time

        with lock:
            output_frame = frame.copy()


# ===========================================================================
# 4. MJPEG STREAMING ENDPOINTS
# ===========================================================================
def _generate_mjpeg(get_frame):
    while True:
        with lock:
            frame = get_frame()
            if frame is None:
                continue
            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded) + b'\r\n')
        time.sleep(0.05)


@app.get("/live-feed")
def video_feed():
    return StreamingResponse(_generate_mjpeg(lambda: output_frame),
                              media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/live-feed-raw")
def raw_video_feed():
    return StreamingResponse(_generate_mjpeg(lambda: raw_output_frame),
                              media_type="multipart/x-mixed-replace; boundary=frame")


# ===========================================================================
# 5. STARTUP
# ===========================================================================
if __name__ == "__main__":
    ai_thread = threading.Thread(target=ai_processing_loop, daemon=True)
    ai_thread.start()
    print("\n🚀 [NETRA UNIFIED] Engine running — CPU mode, 3-sec anti-flicker SOS.")
    print("📺 AI feed:   http://127.0.0.1:8001/live-feed")
    print("📺 Raw feed:  http://127.0.0.1:8001/live-feed-raw\n")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")