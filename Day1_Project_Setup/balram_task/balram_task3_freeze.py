import cv2
import time
import os
import numpy as np
import threading
from dotenv import load_dotenv

from ai_processor import process_frame
from api_service import send_alert_async

class CameraStream:
    def __init__(self, src):
        self.stream = cv2.VideoCapture(src)
        if self.stream.isOpened():
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            (self.grabbed, self.frame) = self.stream.read()
        else:
            self.grabbed = False
            self.frame = None
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            if self.stream.isOpened():
                try:
                    (self.grabbed, self.frame) = self.stream.read()
                except Exception:
                    self.grabbed = False
            else:
                time.sleep(0.5)

    def read(self):
        return self.grabbed, self.frame

    def stop(self):
        self.stopped = True
        if self.stream and self.stream.isOpened():
            self.stream.release()

load_dotenv()
CAMERA_1_URL = os.getenv("CAMERA_1_URL")
CAMERA_2_URL = os.getenv("CAMERA_2_URL")

print("System Initializing: Thermal & Memory Profiling Active...")
cap1 = CameraStream(CAMERA_1_URL).start()
cap2 = CameraStream(CAMERA_2_URL).start()

LAST_ALERT_TIME = 0
COOLDOWN_SECONDS = 5
FRAME_SKIP = 3
frame_count = 0

count1, count2 = 0, 0
boxes1, boxes2 = [], []

# Default resolution scale
ai_resolution_scale = 1.0  

window_name = "Netra AI Pipeline - Hardware Freeze (Balram)"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
is_fullscreen = False

print("System is LIVE! Press 'f' to toggle Full Screen, and 'q' to quit.")

while True:
    success1, frame1 = cap1.read()
    success2, frame2 = cap2.read()
    
    if frame1 is None or not success1:
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame1, "CAM 1 OFFLINE", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        count1, boxes1 = 0, []
    
    if frame2 is None or not success2:
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame2, "CAM 2 OFFLINE", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        count2, boxes2 = 0, []
        
    frame_count += 1
    
    if frame_count % FRAME_SKIP == 0:
        try:
            # Resolution scaling logic for thermal protection
            if ai_resolution_scale < 1.0:
                process_f1 = cv2.resize(frame1, (0, 0), fx=ai_resolution_scale, fy=ai_resolution_scale) if frame1.any() else frame1
                process_f2 = cv2.resize(frame2, (0, 0), fx=ai_resolution_scale, fy=ai_resolution_scale) if frame2.any() else frame2
            else:
                process_f1, process_f2 = frame1, frame2

            if process_f1.any():
                count1, boxes1_raw = process_frame(process_f1)
                boxes1 = [(int(x1/ai_resolution_scale), int(y1/ai_resolution_scale), int(x2/ai_resolution_scale), int(y2/ai_resolution_scale)) for (x1, y1, x2, y2) in boxes1_raw]
            
            if process_f2.any():
                count2, boxes2_raw = process_frame(process_f2)
                boxes2 = [(int(x1/ai_resolution_scale), int(y1/ai_resolution_scale), int(x2/ai_resolution_scale), int(y2/ai_resolution_scale)) for (x1, y1, x2, y2) in boxes2_raw]

        except Exception as e:
            # If GPU memory peaks or AI crashes, auto-downscale the resolution to 50%
            print("⚠️ GPU Memory/Thermal Peak Detected! Auto-downscaling resolution to prevent crash...")
            ai_resolution_scale = 0.5
            time.sleep(0.5) 

    for (x1, y1, x2, y2) in boxes1:
        cv2.rectangle(frame1, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(frame1, f"Cam 1 Persons: {count1}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    for (x1, y1, x2, y2) in boxes2:
        cv2.rectangle(frame2, (x1, y1), (x2, y2), (255, 0, 0), 2)
    cv2.putText(frame2, f"Cam 2 Persons: {count2}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    total_persons = count1 + count2
    if total_persons >= 2:
        current_time = time.time()
        if (current_time - LAST_ALERT_TIME) > COOLDOWN_SECONDS:
            alert_payload = {
                "event_type": "THREAT_DETECTED",
                "source": "dual_cam_setup_freeze",
                "details": {
                    "persons_in_frame": total_persons,
                    "timestamp": current_time,
                    "severity": "HIGH"
                }
            }
            send_alert_async(alert_payload)
            LAST_ALERT_TIME = current_time

    frame1_resized = cv2.resize(frame1, (640, 480))
    frame2_resized = cv2.resize(frame2, (640, 480))
    combined_frame = np.hstack((frame1_resized, frame2_resized))

    if ai_resolution_scale < 1.0:
        cv2.putText(combined_frame, "WARNING: SYSTEM DOWNSCALED (THERMAL PROTECT)", (150, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

    cv2.imshow(window_name, combined_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('f'): 
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

cap1.stop()
cap2.stop()
cv2.destroyAllWindows()