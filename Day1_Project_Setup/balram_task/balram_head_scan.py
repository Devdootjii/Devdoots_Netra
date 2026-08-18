import cv2
import time
import os
import numpy as np
from dotenv import load_dotenv

from ai_processor import process_frame
from api_service import send_alert_async

# --- SETUP ---
load_dotenv()
CAMERA_1_URL = os.getenv("CAMERA_1_URL")
CAMERA_2_URL = os.getenv("CAMERA_2_URL")

print("Connecting to Dual CCTV feeds...")
cap1 = cv2.VideoCapture(CAMERA_1_URL)
cap2 = cv2.VideoCapture(CAMERA_2_URL)

LAST_ALERT_TIME = 0
COOLDOWN_SECONDS = 5
FRAME_SKIP = 3
frame_count = 0

# --- INITIALIZE VARIABLES (ERROR FIX) ---
count1, count2 = 0, 0
boxes1, boxes2 = [], []

# --- UI SETUP ---
window_name = "Netra AI Pipeline - Dual CCTV (Balram)"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
is_fullscreen = False

print("System is LIVE! Press 'f' to toggle Full Screen, and 'q' to quit.")

while cap1.isOpened() and cap2.isOpened():
    success1, frame1 = cap1.read()
    success2, frame2 = cap2.read()
    
    if not success1 or not success2:
        print("Network Drop: Ek camera disconnect ho gaya!")
        break
        
    frame_count += 1
    
    # --- AI PROCESSING (Dono frame ek sath) ---
    if frame_count % FRAME_SKIP == 0:
        count1, boxes1 = process_frame(frame1)
        count2, boxes2 = process_frame(frame2)

    # --- UI DRAWING CAM 1 ---
    for (x1, y1, x2, y2) in boxes1:
        cv2.rectangle(frame1, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(frame1, f"Cam 1 Persons: {count1}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # --- UI DRAWING CAM 2 ---
    for (x1, y1, x2, y2) in boxes2:
        cv2.rectangle(frame2, (x1, y1), (x2, y2), (255, 0, 0), 2)
    cv2.putText(frame2, f"Cam 2 Persons: {count2}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # --- THREAT LOGIC ---
    total_persons = count1 + count2
    if total_persons >= 2:
        current_time = time.time()
        if (current_time - LAST_ALERT_TIME) > COOLDOWN_SECONDS:
            alert_payload = {
                "event_type": "THREAT_DETECTED",
                "source": "dual_cam_setup",
                "details": {
                    "persons_in_frame": total_persons,
                    "timestamp": current_time,
                    "severity": "HIGH"
                }
            }
            print("🚨 THREAT DETECTED! Triggering async alert...")
            send_alert_async(alert_payload)
            LAST_ALERT_TIME = current_time

    # --- RESIZE AND MERGE FRAMES (Side-by-Side UI) ---
    frame1_resized = cv2.resize(frame1, (640, 480))
    frame2_resized = cv2.resize(frame2, (640, 480))
    combined_frame = np.hstack((frame1_resized, frame2_resized))

    cv2.imshow(window_name, combined_frame)

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

cap1.release()
cap2.release()
cv2.destroyAllWindows()