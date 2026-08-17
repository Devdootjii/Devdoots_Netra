import cv2
import time

def run_stress_test():
    # Aapki abnormal video ka path (hand signal for help)
    video_path = 0
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Video nahi khul rahi hai. Path check karein.")
        return

    start_time = time.time()
    test_duration = 10 * 60 # 10 minutes in seconds

    print("🚀 10-Minute Stress Test shuru ho gaya hai...")
    print("Terminal par nazar rakhein ki Telegram/Cloud Upload fail toh nahi ho raha.")

    while (time.time() - start_time) < test_duration:
        ret, frame = cap.read()
        if not ret:
            # Video khatam hone par wapas zero se shuru karein (Loop)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        cv2.imshow('Day 4 - Stress Test (10 Min Loop)', frame)

        # 'q' dabane par test beech mein ruk jayega
        if cv2.waitKey(25) & 0xFF == ord('q'):
            print("Test manually stopped.")
            break

    print("✅ 10-Minute Test poora ho gaya!")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_stress_test()