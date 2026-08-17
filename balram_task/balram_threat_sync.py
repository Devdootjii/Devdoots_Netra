import cv2
import json
import time
import requests
from ultralytics import YOLO

# --- CONFIGURATION ---
# Divyansh ke FastAPI backend ka address (Abhi local network ke liye)
BACKEND_API_URL = "http://localhost:8000/api/alert" 

# AI Model Setup - Using 'n' (nano) model for maximum FPS aur GPU (cuda) par shift kar rahe hain
print("Loading YOLO Model on GPU...")
model = YOLO("yolov8n.pt")
model.to('cuda') # RTX GPU zindabad

# Camera Setup
cap = cv2.VideoCapture(0)

# Cooldown logic taaki API spam na ho (1 alert per 5 seconds)
LAST_ALERT_TIME = 0
COOLDOWN_SECONDS = 5

print("System is LIVE! Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Camera se frame nahi aa raha!")
        break

    # AI Inference (Detection)
    results = model(frame, verbose=False)
    
    person_count = 0
    
    # Har frame mein log (persons) count karna
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # COCO dataset mein Class 0 'Person' hoti hai
            if int(box.cls[0]) == 0: 
                person_count += 1
                
                # Bounding box draw karna (Visuals ke liye)
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, 'Person', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # ---------------------------------------------------------
    # DAY 3 & 4: THREAT LOGIC & SECURE JSON DATA STREAM
    # ---------------------------------------------------------
    
    # Abhi ke liye THREAT tab maana jayega jab camera mein 2 ya usse zyada log dikhein 
    # (Baad mein Ritesh ka MediaPipe SOS logic yahan jodd(merge) denge)
    threat_detected = (person_count >= 2)

    if threat_detected:
        current_time = time.time()
        
        # Check karenge ki kya pichle alert se 5 second guzar chuke hain (Spam protection)
        if (current_time - LAST_ALERT_TIME) > COOLDOWN_SECONDS:
            
            # Day 4: AI output ko structured JSON format mein convert karna
            alert_payload = {
                "event_type": "THREAT_DETECTED",
                "source": "balram_yolo_cam_1",
                "details": {
                    "persons_in_frame": person_count,
                    "timestamp": current_time,
                    "severity": "HIGH"
                }
            }
            
            # API Request bhejna[cite: 2]
            try:
                print(f"🚨 THREAT DETECTED! Sending JSON to Backend... -> {json.dumps(alert_payload)}")
                response = requests.post(BACKEND_API_URL, json=alert_payload, timeout=2)
                
                if response.status_code == 200:
                    print("✅ Backend ne alert receive kar liya!")
                else:
                    print(f"⚠️ Backend error: {response.status_code}")
            
            except requests.exceptions.RequestException as e:
                # Agar Divyansh ka server band hua toh code crash nahi hoga
                print("❌ Backend is offline. Alert logging failed.")
            
            # Alert time update karna taaki next alert 5 sec baad hi jaye
            LAST_ALERT_TIME = current_time

    # Screen par display
    cv2.putText(frame, f"Persons: {person_count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Netra AI Pipeline - Balram", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()