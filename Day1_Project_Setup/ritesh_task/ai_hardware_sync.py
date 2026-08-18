import cv2
import time
import threading
import requests
import os
from datetime import datetime
import mediapipe as mp
from ultralytics import YOLO
from dotenv import load_dotenv

# ==========================================
# 0. LOAD ENVIRONMENT VARIABLES
# ==========================================
load_dotenv()
YOLO_PATH = os.getenv("MODEL_PATH")
CAMERA_1_URL = os.getenv("CAMERA_1_URL")
BACKEND_EVENT_URL = os.getenv("BACKEND_EVENT_URL")

if not YOLO_PATH or not CAMERA_1_URL:
    print("❌ ERROR: Check .env file. MODEL_PATH or CAMERA_1_URL missing!")
    exit()

# ==========================================
# 1. BALRAM'S ZERO-LAG CAMERA STREAM CLASS (WITH RITESH'S FIX)
# ==========================================
class CameraStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        # Buffer clear for zero lag
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        time.sleep(0.1)  # Ritesh's Fix: Wait for background thread to finish cleanly
        if self.stream.isOpened():
            self.stream.release()

# ==========================================
# 2. AI MODELS INITIALIZATION
# ==========================================
print(f"[NETRA ENGINE] Loading YOLOv8 from: {YOLO_PATH} ...")
yolo_model = YOLO(YOLO_PATH)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=0, 
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ==========================================
# 3. CAMERA & STATE CONTROLLERS
# ==========================================
print(f"[NETRA ENGINE] Connecting to IP Camera: {CAMERA_1_URL} ...")
cam = CameraStream(CAMERA_1_URL).start()
time.sleep(2.0)

window_title = "NETRA AI | IP Camera Sync"
cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

sos_hold_start = None
REQUIRED_HOLD_SEC = 2.5
ALERT_COOLDOWN_SEC = 5.0
last_alert_time = 0
frame_idx = 0
SKIP_INTERVAL = 3
prev_tick = time.time()

current_resolution_scale = 1.0
cached_boxes = []
cached_p_count = 0
cached_threat_active = False
cached_landmarks = None

print("[NETRA ENGINE] Hardware Integration Active. System is Live.")

# ==========================================
# 4. MAIN THREAD EVENT LOOP
# ==========================================
while True:
    frame = cam.read()
    if frame is None:
        print("⚠️ Camera Feed Lost! Attempting to reconnect...")
        time.sleep(1)
        continue

    if current_resolution_scale < 1.0:
        h, w = frame.shape[:2]
        frame = cv2.resize(frame, (int(w * current_resolution_scale), int(h * current_resolution_scale)))

    frame = cv2.flip(frame, 1)
    now = time.time()
    frame_idx += 1

    time_diff = now - prev_tick
    fps = 1 / time_diff if time_diff > 0 else 0
    prev_tick = now

    try:
        if frame_idx % SKIP_INTERVAL == 0:
            yolo_out = yolo_model(frame, classes=[0], verbose=False)
            cached_boxes = []
            cached_p_count = 0

            for res in yolo_out:
                for b in res.boxes:
                    cached_p_count += 1
                    bx = list(map(int, b.xyxy[0]))
                    cached_boxes.append(bx)

            rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pose_out = pose.process(rgb_img)
            cached_landmarks = pose_out.pose_landmarks
            cached_threat_active = False

            if cached_landmarks:
                lm = cached_landmarks.landmark
                l_sh_y = lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y
                r_sh_y = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
                l_wr_y = lm[mp_pose.PoseLandmark.LEFT_WRIST].y
                r_wr_y = lm[mp_pose.PoseLandmark.RIGHT_WRIST].y

                if (l_wr_y < l_sh_y) or (r_wr_y < r_sh_y):
                    cached_threat_active = True

    except Exception as e:
        print(f"⚠️ Warning: High Load Detected ({e}). Downscaling resolution to prevent crash...")
        current_resolution_scale = 0.75 
        continue

    for i, (x1, y1, x2, y2) in enumerate(cached_boxes):
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 120, 0), 2)

    if cached_threat_active:
        if sos_hold_start is None:
            sos_hold_start = now
        duration = now - sos_hold_start

        if duration >= REQUIRED_HOLD_SEC:
            cv2.putText(frame, "SOS CONFIRMED (IP CAM)", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 3)
            if now - last_alert_time > ALERT_COOLDOWN_SEC:
                print(f"🔥 [ALERT] Cam 1 (IP) detected SOS with {cached_p_count} person(s).")
                last_alert_time = now
        else:
            cv2.putText(frame, f"HOLD GESTURE ({duration:.1f}s)", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 165, 255), 2)
    else:
        sos_hold_start = None
        cv2.putText(frame, "IP CAMERA LIVE", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    cv2.putText(frame, f"FPS: {int(fps)}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 0), 2)
    
    cv2.imshow(window_title, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.stop()
cv2.destroyAllWindows()
pose.close()