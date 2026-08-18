import os
from ultralytics import YOLO
from dotenv import load_dotenv

# .env se Model Path load karna
load_dotenv()
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")

print(f"Loading YOLO Model from: {MODEL_PATH} on GPU...")
model = YOLO(MODEL_PATH)
model.to('cuda')

def process_frame(frame, conf_threshold=0.60):
    """
    Frame ko scan karke person count aur unke boxes return karta hai.
    """
    results = model(frame, verbose=False, conf=conf_threshold)
    person_count = 0
    boxes_list = []
    
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0: 
                person_count += 1
                # Box coordinates ko list me save karna
                boxes_list.append(tuple(map(int, box.xyxy[0])))
                
    return person_count, boxes_list