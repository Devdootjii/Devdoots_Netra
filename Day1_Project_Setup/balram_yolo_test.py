import cv2
from ultralytics import YOLO

# Pre-trained YOLO model load kar rahe hain (yolov10n.pt automatically download ho jayega)
# RTX 4050 GPU use karne ke liye device='cuda' lagaya hai taaki zero lag aaye
print("Loading YOLO Model on GPU...")
model = YOLO('yolov10n.pt')  

# Laptop ka default webcam (0) open karna
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Camera open nahi ho raha. Tape toh nahi lagayi webcam par?")
    exit()

print("Camera started! Press 'q' to exit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Failed to grab frame.")
        break

    # AI Detection: classes=[0] ka matlab sirf 'Person' detect karega
    results = model.predict(source=frame, device='cpu', classes=[0], verbose=False)

    # Frame ke upar bounding box draw karna
    annotated_frame = results[0].plot()

    # Screen par live video dikhana
    cv2.imshow("Netra - Day 1 Balram YOLO Test", annotated_frame)

    # 'q' button dabane par camera band ho jayega
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Safely sab kuch close karna
cap.release()
cv2.destroyAllWindows()