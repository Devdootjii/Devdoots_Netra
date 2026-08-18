import cv2
import time
import os
from dotenv import load_dotenv

# Hamari doosri files se functions import kar rahe hain
from ai_processor import process_frame
from api_service import send_alert_async

# --- SETUP ---
load_dotenv()
CAMERA_URL = os.getenv("CAMERA_URL", 0)

print(f"Connecting to Camera feed: {CAMERA_URL}")
cap = cv2.VideoCapture(CAMERA_URL)
LAST_ALERT_TIME = 0
COOLDOWN_SECONDS = 5
FRAME_SKIP = 3
frame_count = 0

current_person_count = 0
current_boxes = []

# --- FULL SCREEN TOGGLE SETUP ---
window_name = "Netra AI Pipeline - Balram"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
is_fullscreen = False

print("System is LIVE! Press 'f' to toggle Full Screen, and 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
        
    frame_count += 1
    
    # --- AI PROCESSING (Calling external file) ---
    if frame_count % FRAME_SKIP == 0:
        # process_frame function 'ai_processor.py' se chal raha hai
        current_person_count, current_boxes = process_frame(frame)

    # --- UI DRAWING ---
    for (x1, y1, x2, y2) in current_boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, 'Person', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # --- THREAT LOGIC & API CALL ---
    threat_detected = (current_person_count >= 2)
    if threat_detected:
        current_time = time.time()
        if (current_time - LAST_ALERT_TIME) > COOLDOWN_SECONDS:
            alert_payload = {
                "event_type": "THREAT_DETECTED",
                "source": "balram_yolo_cam_1",
                "details": {
                    "persons_in_frame": current_person_count,
                    "timestamp": current_time,
                    "severity": "HIGH"
                }
            }
            
            print("🚨 THREAT DETECTED! Triggering async alert...")
            # send_alert_async function 'api_service.py' se chal raha hai
            send_alert_async(alert_payload)
            LAST_ALERT_TIME = current_time

    # Display count and show frame
    cv2.putText(frame, f"Persons: {current_person_count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow(window_name, frame)

    # --- KEYBOARD CONTROLS ---
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('f'): 
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

cap.release()
cv2.destroyAllWindows()