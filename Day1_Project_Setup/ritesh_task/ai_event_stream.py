import cv2
import time
import requests
from datetime import datetime
import mediapipe as mp
from ultralytics import YOLO

# ==========================================
# 1. BACKEND SYNC CONFIGURATION
# ==========================================
BACKEND_EVENT_URL = "http://127.0.0.1:8000/api/ai-stream"
CAMERA_NODE_ID = "Ritesh_Edge_Node_01"

def dispatch_threat_event(person_count, threat_type="SOS_TRIGGERED", confidence=0.95):
    """
    Day 4 Task 1: Event-driven alert dispatch.
    Fires strictly when an active threat is verified.
    """
    payload = {
        "camera_id": CAMERA_NODE_ID,
        "event_type": threat_type,
        "threat_level": "CRITICAL",
        "persons_detected": person_count,
        "confidence_score": confidence,
        "event_timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(BACKEND_EVENT_URL, json=payload, timeout=0.5)
        if response.status_code == 200:
            print(f"🔥 [EVENT DISPATCHED] -> Threat synced to backend at {payload['event_timestamp']}")
        else:
            print(f"⚠️ [BACKEND WARNING] -> Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ [SYNC FAILED] -> Backend unreachable: {e}")

# ==========================================
# 2. AI MODELS INITIALIZATION
# ==========================================
print("[NETRA ENGINE] Loading YOLOv10n & MediaPipe Pose...")
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
# 3. CAMERA & STATE CONTROLLERS
# ==========================================
cap = cv2.VideoCapture(0)
window_title = "NETRA AI | Day 4 Event Stream Engine"
cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

sos_hold_start = None
REQUIRED_HOLD_SEC = 2.5
ALERT_COOLDOWN_SEC = 4.0
last_alert_time = 0

frame_idx = 0
SKIP_INTERVAL = 3
prev_tick = 0

# Cache store
cached_boxes = []
cached_p_count = 0
cached_landmarks = None
cached_threat_active = False

print("[NETRA ENGINE] Event Stream Active. Monitoring for threat triggers...")

# ==========================================
# 4. MAIN EVENT-DRIVEN STREAM LOOP
# ==========================================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    now = time.time()
    frame_idx += 1

    fps = 1 / (now - prev_tick) if prev_tick > 0 else 0
    prev_tick = now

    # --- AI INFERENCE (EVERY 3RD FRAME) ---
    if frame_idx % SKIP_INTERVAL == 0:
        # YOLO Person Detection
        yolo_out = yolo_model(frame, classes=[0], verbose=False)
        cached_boxes = []
        cached_p_count = 0

        for res in yolo_out:
            for b in res.boxes:
                cached_p_count += 1
                bx = list(map(int, b.xyxy[0]))
                cached_boxes.append(bx)

        # MediaPipe Pose Verification
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

    # --- RENDER OVERLAYS ---
    for i, (x1, y1, x2, y2) in enumerate(cached_boxes):
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 120, 0), 2)
        cv2.putText(frame, f"Person {i+1}", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 120, 0), 2)

    if cached_landmarks:
        mp_drawing.draw_landmarks(frame, cached_landmarks, mp_pose.POSE_CONNECTIONS)

    # --- EVENT DISPATCH LOGIC (STRICTLY ON THREAT) ---
    if cached_threat_active:
        if sos_hold_start is None:
            sos_hold_start = now

        duration = now - sos_hold_start

        if duration >= REQUIRED_HOLD_SEC:
            cv2.putText(frame, f"THREAT ACTIVE: SOS CONFIRMED", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 3)

            # Fire HTTP POST strictly when threat is verified and cooldown passed
            if now - last_alert_time > ALERT_COOLDOWN_SEC:
                dispatch_threat_event(person_count=cached_p_count)
                last_alert_time = now
        else:
            cv2.putText(frame, f"HOLD GESTURE TO TRIGGER ({duration:.1f}s)", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 165, 255), 2)
    else:
        sos_hold_start = None
        cv2.putText(frame, "MONITORING ACTIVE (IDLE)", (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    cv2.putText(frame, f"FPS: {int(fps)}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 0), 2)

    cv2.imshow(window_title, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pose.close()