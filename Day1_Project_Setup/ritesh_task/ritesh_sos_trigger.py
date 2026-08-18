import cv2
import time
import mediapipe as mp

# MediaPipe Pose Setup
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)

# Professional Monitoring Title
window_name = "NETRA AI | Live Threat & Pose Monitor"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

# State Management
sos_start_time = None
REQUIRED_HOLD_TIME = 2.5  # Seconds threshold for confirmed gesture
alert_sent = False

print("[NETRA ENGINE] Video Stream Initialized. Monitoring Active...")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("[NETRA ERROR] Video Stream Terminated.")
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)

    current_time = time.time()
    hands_raised = False

    if results.pose_landmarks:
        # Draw clean skeletal mesh
        mp_drawing.draw_landmarks(
            frame, 
            results.pose_landmarks, 
            mp_pose.POSE_CONNECTIONS
        )

        landmarks = results.pose_landmarks.landmark
        l_shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
        r_shoulder_y = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
        l_wrist_y = landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y
        r_wrist_y = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y

        # Hands Raised Detection Rule
        if (l_wrist_y < l_shoulder_y) or (r_wrist_y < r_shoulder_y):
            hands_raised = True

    # Gesture Hold Verification
    if hands_raised:
        if sos_start_time is None:
            sos_start_time = current_time

        elapsed_time = current_time - sos_start_time

        if elapsed_time >= REQUIRED_HOLD_TIME:
            # Active Emergency State
            cv2.putText(frame, "EMERGENCY: SOS SIGNAL DETECTED", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 2)
            
            if not alert_sent:
                print("[ALERT DISPATCH] Confirmed SOS Gesture Detected.")
                alert_sent = True
        else:
            # Gesture Confirmation in Progress
            cv2.putText(frame, f"VERIFYING GESTURE ({elapsed_time:.1f}s)", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 165, 255), 2)
    else:
        # Reset State
        sos_start_time = None
        alert_sent = False
        cv2.putText(frame, "SYSTEM STATUS: SECURE", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    cv2.imshow(window_name, frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pose.close()
print("[NETRA ENGINE] Stream Shutdown Complete.")