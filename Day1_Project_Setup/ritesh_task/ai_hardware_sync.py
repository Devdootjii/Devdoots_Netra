import cv2
import time
import threading
import json
import os
import numpy as np
import mediapipe as mp
from ultralytics import YOLO
from dotenv import load_dotenv

# ==========================================
# 1. LOAD CONFIG & ENVIRONMENT
# ==========================================
load_dotenv()
YOLO_PATH = os.getenv("MODEL_PATH", "../models/yolov8n.pt")
# PDF Task: File located in the root directory[cite: 3]
CONFIG_FILE = "../camera_config.json" 

def get_camera_urls():
    # PDF Task: Read stream sources dynamically[cite: 4]
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                cam1 = data.get("cam_1", 0)
                cam2 = data.get("cam_2", "")
                
                cam1 = int(cam1) if str(cam1).isdigit() else cam1
                cam2 = int(cam2) if str(cam2).isdigit() else cam2
                return cam1, cam2
    except Exception:
        pass
    return 0, ""

# ==========================================
# 2. BULLETPROOF HOT-RELOADING STREAM CLASS
# ==========================================
class CameraStream:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.stream = cv2.VideoCapture(self.url) if str(self.url) != "" else None
        if self.stream and self.stream.isOpened():
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.grabbed = False
        self.frame = None
        self.stopped = False
        self.reloading = False # Safety switch to prevent thread crashes
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def reload_stream(self, new_url):
        # PDF Task: Seamless stream switching without crashing the AI model[cite: 3, 4]
        if str(self.url) != str(new_url):
            print(f"\n🔄 Hot-Reloading {self.name} to new URL...")
            self.reloading = True # Pause background thread
            time.sleep(0.3) # Give it a moment to stop safely
            
            with self.lock:
                self.url = new_url
                if self.stream:
                    self.stream.release() 
                if str(self.url) != "":
                    self.stream = cv2.VideoCapture(self.url)
                    if self.stream.isOpened():
                        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                else:
                    self.stream = None
                    
            self.reloading = False # Resume background thread
            print(f"✅ {self.name} successfully transitioned!")

    def update(self):
        while not self.stopped:
            if self.reloading:
                time.sleep(0.1)
                continue
                
            try:
                if self.stream and self.stream.isOpened():
                    grabbed, frame = self.stream.read()
                    with self.lock:
                        if grabbed:
                            self.grabbed, self.frame = grabbed, frame
                else:
                    time.sleep(0.1)
            except Exception:
                # Catch any OpenCV C++ exceptions during transition silently
                time.sleep(0.1)

    def read(self):
        with self.lock:
            return self.grabbed, self.frame

    def stop(self):
        self.stopped = True
        time.sleep(0.1)
        if self.stream and self.stream.isOpened():
            self.stream.release()

# ==========================================
# 3. INITIALIZE AI MODELS
# ==========================================
print("[NETRA ENGINE] Loading YOLOv8 and Pose Models...")
yolo_model = YOLO(YOLO_PATH)
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# ==========================================
# 4. SYSTEM STARTUP
# ==========================================
url1, url2 = get_camera_urls()
cam1 = CameraStream("Cam 1", url1).start()
cam2 = CameraStream("Cam 2", url2).start()
time.sleep(2.0)

window_title = "Project Netra - Dual Live AI Sync"
cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

# PDF Task: File-watching mechanism/interval polling[cite: 3, 4]
last_mod_time = os.path.getmtime(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else 0
check_interval = 2.0
last_check_time = time.time()
frame_idx = 0

print("🚀 AI System is LIVE! Dual Architecture active.")

# ==========================================
# 5. MAIN EVENT LOOP & AI PROCESSING
# ==========================================
while True:
    now = time.time()

    # Day 6 Polling: Detect changes without restarting script[cite: 3, 4]
    if now - last_check_time > check_interval:
        if os.path.exists(CONFIG_FILE):
            current_mod_time = os.path.getmtime(CONFIG_FILE)
            if current_mod_time != last_mod_time:
                last_mod_time = current_mod_time
                n_url1, n_url2 = get_camera_urls()
                cam1.reload_stream(n_url1)
                cam2.reload_stream(n_url2)
        last_check_time = now

    frame_idx += 1
    
    # Process Cam 1
    grabbed1, f1 = cam1.read()
    if grabbed1 and f1 is not None:
        f1 = cv2.flip(f1, 1) # Fix Mirror Issue
        f1 = cv2.resize(f1, (640, 480))
        cached_threat1 = False
        
        # AI Logic for Cam 1
        if frame_idx % 3 == 0:
            results = yolo_model(f1, classes=[0], verbose=False)
            for r in results:
                for b in r.boxes:
                    x1, y1, x2, y2 = map(int, b.xyxy[0])
                    cv2.rectangle(f1, (x1, y1), (x2, y2), (255, 120, 0), 2)
            
            rgb = cv2.cvtColor(f1, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)
            if res.pose_landmarks:
                mp_drawing.draw_landmarks(f1, res.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                lm = res.pose_landmarks.landmark
                l_sh, r_sh = lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y, lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
                l_wr, r_wr = lm[mp_pose.PoseLandmark.LEFT_WRIST].y, lm[mp_pose.PoseLandmark.RIGHT_WRIST].y
                if (l_wr < l_sh) or (r_wr < r_sh):
                    cached_threat1 = True

        if cached_threat1:
            cv2.putText(f1, "SOS THREAT DETECTED!", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        else:
            cv2.putText(f1, "CAM 1 | AI SECURE", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        f1 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(f1, "CAM 1 OFFLINE / RELOADING", (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Process Cam 2
    grabbed2, f2 = cam2.read()
    if grabbed2 and f2 is not None:
        f2 = cv2.flip(f2, 1)
        f2 = cv2.resize(f2, (640, 480))
        cv2.putText(f2, "CAM 2 | LIVE FEED", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    else:
        f2 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(f2, "CAM 2 OFFLINE / RELOADING", (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Combine frames horizontally (Dual Screen Mode)
    combined_frame = np.hstack((f1, f2))
    cv2.imshow(window_title, combined_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam1.stop()
cam2.stop()
cv2.destroyAllWindows()
pose.close()