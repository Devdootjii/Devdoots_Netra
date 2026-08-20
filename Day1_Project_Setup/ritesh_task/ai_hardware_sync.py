import cv2
import time
import threading
import json
import os
import requests
import mediapipe as mp
from ultralytics import YOLO
from dotenv import load_dotenv

# ==========================================
# 1. LOAD CONFIG & ENVIRONMENT
# ==========================================
load_dotenv()
YOLO_PATH = os.getenv("MODEL_PATH", "../models/yolov8n.pt")
CONFIG_FILE = "../camera_config.json" 
# PDF Phase 2: Target FastAPI server URL
BACKEND_API_URL = "http://127.0.0.1:8000/api/ai-stream"

def get_camera_urls():
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
# 2. API CLIENT (Send Data to Backend)
# ==========================================
def send_detection_data(cam_id, loc_name, threat_level, persons, is_sos):
    # PDF Phase 2: Send POST request with JSON structure
    payload = {
        "camera_id": cam_id,
        "location_name": loc_name,
        "threat_level": threat_level,
        "persons_detected": persons,
        "sos_active": is_sos # Phase 4: Flags the backend for Telegram alert
    }
    try:
        # Use a short timeout so AI loop doesn't lag if backend is slow
        requests.post(BACKEND_API_URL, json=payload, timeout=1.0)
        print(f"[{cam_id}] API Synced | Persons: {persons} | SOS: {is_sos}")
    except requests.exceptions.RequestException:
        print(f"[{cam_id}] Warning: Backend unreachable at {BACKEND_API_URL}")

# ==========================================
# 3. HOT-RELOADING STREAM CLASS
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
        self.reloading = False 
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def reload_stream(self, new_url):
        # Phase 3: Hot-Reloading using cap.release()[cite: 6]
        if str(self.url) != str(new_url):
            print(f"\n🔄 Hot-Reloading {self.name} to new URL...")
            self.reloading = True 
            time.sleep(0.3) 
            
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
                    
            self.reloading = False 
            print(f"✅ {self.name} transition complete!")

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
# 4. INITIALIZE AI MODELS
# ==========================================
print("[NETRA ENGINE] Loading Headless YOLOv8 and Pose Models...")
yolo_model = YOLO(YOLO_PATH)
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

url1, url2 = get_camera_urls()
cam1 = CameraStream("Cam 1", url1).start()
cam2 = CameraStream("Cam 2", url2).start()
time.sleep(2.0)

# Phase 3: Loop reloads every 5 seconds[cite: 6]
check_interval = 5.0
last_check_time = time.time()
last_mod_time = os.path.getmtime(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else 0
frame_idx = 0

# 2.5 Second Hold Logic Variables
cached_threat1 = False
sos_start_time = 0
is_sos_holding = False

print("🚀 Headless AI System is LIVE! Sending data to Backend API...")

# ==========================================
# 5. MAIN HEADLESS AI LOOP
# ==========================================
while True:
    now = time.time()

    # Dynamic Config Polling (Phase 3)[cite: 6]
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
    
    # Process Cam 1 Data (No Display)
    grabbed1, f1 = cam1.read()
    if grabbed1 and f1 is not None:
        f1 = cv2.flip(f1, 1) 
        
        # Only process every 10th frame for the API to avoid spamming the backend
        if frame_idx % 10 == 0:
            persons_count = 0 
            gesture_detected_this_frame = False
            
            # Detect Persons
            results = yolo_model(f1, classes=[0], verbose=False)
            for r in results:
                persons_count += len(r.boxes)
            
            # Detect Pose (SOS)
            rgb = cv2.cvtColor(f1, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)
            if res.pose_landmarks:
                lm = res.pose_landmarks.landmark
                l_sh, r_sh = lm[11].y, lm[12].y
                l_wr, r_wr = lm[15].y, lm[16].y
                
                if (l_wr < l_sh) or (r_wr < r_sh):
                    gesture_detected_this_frame = True

            # The 2.5 Seconds Hold Logic
            if gesture_detected_this_frame:
                if not is_sos_holding:
                    is_sos_holding = True
                    sos_start_time = time.time()
                elif time.time() - sos_start_time >= 2.5:
                    cached_threat1 = True
            else:
                is_sos_holding = False
                sos_start_time = 0
                cached_threat1 = False

            # Dispatch API Request in background
            threat_level = "CRITICAL" if cached_threat1 else "SAFE"
            threading.Thread(
                target=send_detection_data, 
                args=("CAM 01", "Main Entrance", threat_level, persons_count, cached_threat1),
                daemon=True
            ).start()

    time.sleep(0.01) # Small sleep to stabilize CPU loop

cam1.stop()
cam2.stop()
pose.close()