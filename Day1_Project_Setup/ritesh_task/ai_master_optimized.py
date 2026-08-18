import cv2
import time
import requests
from datetime import datetime
import mediapipe as mp
from ultralytics import YOLO

# ==========================================
# 1. DIVYANSH FASTAPI BACKEND CONFIG
# ==========================================
BACKEND_API_URL = "http://127.0.0.1:8000/api/ai-stream"
CAMERA_ID = "Ritesh_Master_Node"

def send_alert_to_backend(is_sos, threat_lvl, person_count):
    payload = {
        "camera_id": CAMERA_ID,
        "threat_level": threat_lvl,
        "persons_detected": person_count,
        "sos_active": is_sos,
        "frame_timestamp": datetime.now().isoformat()
    }
    try:
        response = requests.post(BACKEND_API_URL, json=payload, timeout=0.3)
        if response.status_code == 200:
            print(f"[NETRA SYNC] Alert Sent -> Backend Status: {response.json().get('status')}")
    except Exception:
        pass 

# ==========================================
# 2. AI MODELS SETUP
# ==========================================
print("[NETRA ENGINE] Loading YOLOv10n Model...")
yolo_model = YOLO("yolov10n.pt") 

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ==========================================
# 3. CAMERA & STATE INITIALIZATION
# ==========================================
cap = cv2.VideoCapture(0)
window_name = "NETRA AI | Live Threat & Crowd Monitor (Optimized)"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

sos_start_time = None
REQUIRED_HOLD_TIME = 2.5
alert_cooldown = 0  

# --- FPS & FRAME SKIPPING VARIABLES ---
frame_counter = 0
SKIP_FRAMES = 3  # Process AI every 3rd frame to maintain 20-25 FPS
prev_frame_time = 0

# Cache variables to prevent flickering on skipped frames
cached_bboxes = []
cached_person_count = 0
cached_pose_landmarks = None
cached_hands_raised = False

print("[NETRA ENGINE] Optimized Pipeline Active. Press 'q' to quit.")

# ==========================================
# 4. REAL-TIME MASTER LOOP (OPTIMIZED)
# ==========================================
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    current_time = time.time()
    frame_counter += 1
    
    # Calculate FPS
    fps = 1 / (current_time - prev_frame_time) if prev_frame_time > 0 else 0
    prev_frame_time = current_time

    # ==================================================
    # AI PROCESSING LOGIC (RUNS ONLY EVERY 3RD FRAME)
    # ==================================================
    if frame_counter % SKIP_FRAMES == 0:
        
        # 1. YOLO PERSON COUNTING
        yolo_results = yolo_model(frame, classes=[0], verbose=False)
        cached_bboxes = []
        cached_person_count = 0
        
        for r in yolo_results:
            for box in r.boxes:
                cached_person_count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cached_bboxes.append((x1, y1, x2, y2))

        # 2. MEDIAPIPE SOS TRACKING
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pose_results = pose.process(rgb_frame)
        cached_pose_landmarks = pose_results.pose_landmarks
        cached_hands_raised = False

        if cached_pose_landmarks:
            landmarks = cached_pose_landmarks.landmark
            l_shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
            r_shoulder_y = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
            l_wrist_y = landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y
            r_wrist_y = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y

            if (l_wrist_y < l_shoulder_y) or (r_wrist_y < r_shoulder_y):
                cached_hands_raised = True

    # ==================================================
    # DRAWING CACHED RESULTS (RUNS ON EVERY FRAME)
    # ==================================================
    
    # Draw YOLO Bounding Boxes
    for i, (x1, y1, x2, y2) in enumerate(cached_bboxes):
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 100, 0), 2)
        cv2.putText(frame, f"Person {i+1}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 2)

    # Draw MediaPipe Landmarks
    if cached_pose_landmarks:
        mp_drawing.draw_landmarks(frame, cached_pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # SOS Logic & Backend Dispatch
    if cached_hands_raised:
        if sos_start_time is None:
            sos_start_time = current_time
        elapsed_time = current_time - sos_start_time

        if elapsed_time >= REQUIRED_HOLD_TIME:
            cv2.putText(frame, f"EMERGENCY: SOS DETECTED | P-Count: {cached_person_count}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 3)
            
            if current_time - alert_cooldown > 2.0:
                send_alert_to_backend(is_sos=True, threat_lvl="CRITICAL", person_count=cached_person_count)
                alert_cooldown = current_time
        else:
            cv2.putText(frame, f"VERIFYING GESTURE ({elapsed_time:.1f}s)", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 165, 255), 2)
    else:
        sos_start_time = None
        cv2.putText(frame, f"SYSTEM SECURE | Persons: {cached_person_count}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    # Display Live FPS on Screen
    cv2.putText(frame, f"FPS: {int(fps)}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 0), 2)

    cv2.imshow(window_name, frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pose.close()