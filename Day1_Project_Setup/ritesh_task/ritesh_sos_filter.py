import cv2
import mediapipe as mp

# MediaPipe Pose & Drawing utilities
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Pose model initialization
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)
window_name = "NETRA | SOS Gesture & Landmark Filter"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

print("[NETRA SYSTEM] Initializing Pose Stream... Press 'q' to disconnect.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("[ERROR] Camera feed unavailable. Exiting...")
        break

    # Flip horizontally for natural stream view
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process Pose landmarks
    results = pose.process(rgb_frame)

    if results.pose_landmarks:
        # Draw skeleton connections
        mp_drawing.draw_landmarks(
            frame, 
            results.pose_landmarks, 
            mp_pose.POSE_CONNECTIONS
        )

        landmarks = results.pose_landmarks.landmark

        # Extract Y-coordinates for Left/Right Shoulders (11, 12) & Wrists (15, 16)
        left_shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
        right_shoulder_y = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y
        left_wrist_y = landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y
        right_wrist_y = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y

        # SOS detection logic: In computer vision, Y decreases as hands move UP
        hands_raised = (left_wrist_y < left_shoulder_y) or (right_wrist_y < right_shoulder_y)
        status = "HANDS RAISED (SOS TRIGGER)" if hands_raised else "NORMAL"

        # Filtered console logging
        print(f"[NETRA SOS] L_Shoulder_Y: {left_shoulder_y:.2f} | R_Shoulder_Y: {right_shoulder_y:.2f} | "
              f"L_Wrist_Y: {left_wrist_y:.2f} | R_Wrist_Y: {right_wrist_y:.2f} | Status: {status}")

    cv2.imshow(window_name, frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pose.close()
print("[NETRA SYSTEM] Stream closed safely.")