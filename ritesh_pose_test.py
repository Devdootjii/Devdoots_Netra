import cv2
import mediapipe as mp

# MediaPipe Hands Setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)
window_name = "NETRA | Live Surveillance & Gesture Stream"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

print("[NETRA SYSTEM] Initializing Camera Stream... Press 'q' to disconnect feed.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("[ERROR] Camera feed unavailable. Disconnecting...")
        break

    # Flip horizontally for natural mirror view
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process hand landmarks
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, 
                hand_landmarks, 
                mp_hands.HAND_CONNECTIONS
            )
            
            wrist = hand_landmarks.landmark[0]
            index_tip = hand_landmarks.landmark[8]
            print(f"[NETRA TRACKER] Wrist: (x={wrist.x:.2f}, y={wrist.y:.2f}) | Index Tip: (x={index_tip.x:.2f}, y={index_tip.y:.2f})")

    cv2.imshow(window_name, frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
print("[NETRA SYSTEM] Stream closed safely.")