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

# FIX (ROOT CAUSE): pehle yahan relative path tha -
# os.path.join(os.path.dirname(__file__), "..", "camera_config.json") - jo
# main.py ki ~/.netra/camera_config.json se BILKUL ALAG file thi. Isliye
# frontend se aaya phone URL kabhi engine tak pahuchta hi nahi tha, aur
# get_camera_url() fallback me 0 (laptop webcam) return karta rehta tha.
# Ab dono files EXACT same absolute path resolve karte hain (main.py wali
# NETRA_HOME/NETRA_CONFIG_PATH env-var logic yahan bhi copy ki hai).
NETRA_HOME = os.environ.get("NETRA_HOME", os.path.join(os.path.expanduser("~"), ".netra"))
CONFIG_PATH = os.environ.get("NETRA_CONFIG_PATH", os.path.join(NETRA_HOME, "camera_config.json"))
print(f"[NETRA ENGINE] camera_config.json path -> {CONFIG_PATH}")

BACKEND_API_URL = "http://127.0.0.1:8000/api/ai-stream"

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

print("[NETRA ENGINE] Initializing YOLOv8-Pose on CPU...")
try:
    pose_model = YOLO("yolov8n-pose.pt")
    pose_model.to("cpu")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit()

output_frame = None
raw_frame = None  # FIX: unprocessed frame, stored so we can serve it to the
                   # frontend's raw preview too - see architecture note below.
lock = threading.Lock()

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
class MJPEGStreamReader:
    """
    FIX (REAL ROOT CAUSE of permanent "CAMERA OFFLINE"): DroidCam's /video
    endpoint sends a `multipart/x-mixed-replace` HTTP stream. Browsers (and
    the frontend's plain <img src=...> tag) understand this format natively -
    that's why the raw feed always showed up fine. But cv2.VideoCapture
    (with or without CAP_FFMPEG) generally cannot demux multipart/x-mixed-
    replace at all - it expects a single continuous MJPEG/video stream, not
    HTTP multipart boundaries. That mismatch is why every single read() kept
    failing no matter how many times we reconnected - it was never a network
    problem. This class instead reads the raw HTTP bytes directly with
    `requests` and manually extracts each JPEG frame between its start
    (0xFFD8) and end (0xFFD9) markers, then decodes it with cv2.imdecode.
    Same .isOpened()/.read()/.release() interface as cv2.VideoCapture so
    nothing else in the loop below needs to change.
    """
    def __init__(self, url, timeout=5):
        self.url = url
        self.timeout = timeout
        self._resp = None
        self._stream = None
        self._buf = b""
        self._opened = False
        self._connect()

    def _connect(self):
        try:
            self._resp = requests.get(self.url, stream=True, timeout=self.timeout)
            self._resp.raise_for_status()
            self._stream = self._resp.raw
            self._buf = b""
            self._opened = True
        except Exception as e:
            # FIX: pehle yahan "except Exception: pass" tha - koi bhi connection
            # error (timeout, connection refused, DNS fail, 404, etc.) chupp-chaap
            # nigal liya jaata tha aur sirf generic "reconnecting" print hota tha.
            # Ab exact reason terminal me dikhega - isse pata chalega ye asli
            # network/host problem hai ya kuch aur.
            print(f"[NETRA ENGINE] Connect failed for {self.url} -> {type(e).__name__}: {e}")
            self._opened = False

    def isOpened(self):
        return self._opened

    def read(self):
        if not self._opened or self._stream is None:
            return False, None
        try:
            while True:
                chunk = self._stream.read(2048)
                if not chunk:
                    self._opened = False
                    return False, None
                self._buf += chunk

                start = self._buf.find(b"\xff\xd8")
                end = self._buf.find(b"\xff\xd9")
                if start != -1 and end != -1 and end > start:
                    jpg = self._buf[start:end + 2]
                    self._buf = self._buf[end + 2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        return True, frame
                    # corrupt frame, keep reading for the next boundary
                elif len(self._buf) > 5_000_000:
                    # safety valve: no valid JPEG found in 5MB, buffer is junk
                    self._buf = b""
        except Exception as e:
            print(f"[NETRA ENGINE] Read failed for {self.url} -> {type(e).__name__}: {e}")
            self._opened = False
            return False, None

    def release(self):
        try:
            if self._resp is not None:
                self._resp.close()
        except Exception:
            pass
        self._opened = False


def open_capture(url):
    """
    HTTP(S) URLs (DroidCam etc.) -> manual MJPEG multipart reader (see above).
    Anything else (e.g. int 0 = local webcam) -> normal cv2.VideoCapture.
    """
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return MJPEGStreamReader(url)
    return cv2.VideoCapture(url)


def ai_processing_loop():
    global output_frame, raw_frame, lock

    current_url = get_camera_url()
    cap = open_capture(current_url)

    last_alert_time = 0
    sos_start_time = None
    last_gesture_time = 0

    # FIX (ROOT CAUSE of permanent "CAMERA OFFLINE"): pehle cap sirf tab dobara
    # banta tha jab config ka URL badalta tha. Agar URL SAHI tha lekin cap
    # pehli hi baar khulne me fail ho gaya (network thoda late aaya / DroidCam
    # app tab tak ready nahi tha), to cap.read() hamesha False deta rehta tha
    # aur engine kabhi dobara connect try hi nahi karta tha - URL same hone
    # tak. Ab har failed read ke baad, thodi der (RECONNECT_INTERVAL) wait
    # karke khud hi reconnect try karta hai, chahe URL na bhi badla ho.
    RECONNECT_INTERVAL = 3.0
    last_reconnect_attempt = 0

    while True:
        new_url = get_camera_url()
        if new_url != current_url:
            cap.release()
            current_url = new_url
            cap = open_capture(current_url)
            time.sleep(1)

        success, frame = cap.read()
        current_time = time.time()

        if not success:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "CAMERA OFFLINE OR LOADING...", (50, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            with lock:
                raw_frame = frame.copy()

            # FIX: agar read fail ho raha hai (URL same hai, cap khula ya nahi khula),
            # periodically reconnect try karo instead of giving up forever.
            if current_time - last_reconnect_attempt > RECONNECT_INTERVAL:
                print(f"[NETRA ENGINE] Frame read failed, reconnecting: {current_url}")
                cap.release()
                cap = open_capture(current_url)
                last_reconnect_attempt = current_time

            # FIX: pehle camera down hone par backend ko kabhi update hi nahi milta tha,
            # so frontend purana (stale) count/SOS state dikhata rehta tha. Ab reset+report karo.
            sos_start_time = None
            if (current_time - last_alert_time > ALERT_COOLDOWN_SEC):
                threading.Thread(target=send_status_to_backend, args=(0, False, False), daemon=True).start()
                last_alert_time = current_time

            time.sleep(0.5)
        else:
            frame = cv2.resize(frame, (640, 480))
            frame_area = frame.shape[0] * frame.shape[1]

            # FIX: save the clean frame BEFORE any boxes/skeleton get drawn on
            # it below, so the raw-feed endpoint can serve an unprocessed
            # preview - the whole point is DroidCam only allows ONE client
            # connected at a time, so nothing except this engine should ever
            # open a direct connection to the phone.
            with lock:
                raw_frame = frame.copy()

            # FIX: explicit conf/iou so low-confidence "ghost" detections don't count as persons
            results = pose_model(frame, verbose=False, device="cpu",
                                  conf=PERSON_CONF_THRESH, iou=PERSON_IOU_THRESH)

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
# 3. VIDEO STREAMING ENDPOINTS (MJPEG)
# ==========================================
def _mjpeg_generator(get_frame):
    while True:
        with lock:
            frame = get_frame()
            if frame is None:
                continue
            flag, encoded_image = cv2.imencode(".jpg", frame)
            if not flag:
                continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n')

        time.sleep(0.05)

@app.get("/live-feed")
def video_feed():
    """Processed feed - YOLO boxes + pose skeleton drawn on top."""
    return StreamingResponse(_mjpeg_generator(lambda: output_frame),
                              media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/raw-feed")
def raw_video_feed():
    """
    FIX: unprocessed passthrough feed, served from HERE (engine) instead of
    the frontend connecting to the phone's DroidCam URL directly. DroidCam
    only allows one connected client at a time - if the frontend's raw
    preview AND this engine both try to open http://phone:4747/video
    directly, one of them gets DroidCam's "busy, take over?" HTML page
    instead of video. Now only this engine ever touches the phone URL, and
    the frontend gets its raw preview from here too.
    """
    return StreamingResponse(_mjpeg_generator(lambda: raw_frame),
                              media_type="multipart/x-mixed-replace; boundary=frame")


# ==========================================
# 4. SERVER STARTUP
# ==========================================
if __name__ == "__main__":
    ai_thread = threading.Thread(target=ai_processing_loop, daemon=True)
    ai_thread.start()

    print("\n🚀 [NETRA UNIFIED] AI Engine Running (CPU Mode + Anti-Flicker 3-Sec Logic)!")
    print("📺 Live Feed URL: http://127.0.0.1:8001/live-feed")
    print("📺 Raw Feed URL:  http://127.0.0.1:8001/raw-feed\n")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")