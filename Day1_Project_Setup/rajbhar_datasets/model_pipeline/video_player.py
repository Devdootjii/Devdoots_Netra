import cv2

def get_abnormal_video_feed():
    """
    Yeh function Balram aur Ritesh ke scripts ko webcam ki jagah
    abnormal video ka feed dega.
    """
    # Aapka sahi video path (Downloads wala)
    video_path = r"C:\Users\atulkumar\Downloads\sos_video.mp4.mp4"
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Video '{video_path}' nahi khul rahi hai.")
        return None
        
    print("Video pipeline ready hai! Sending feed to YOLO/MediaPipe...")
    return cap

# Yeh hissa sirf tab chalega jab aap is file ko khud test karenge
if __name__ == "__main__":
    test_cap = get_abnormal_video_feed()
    if test_cap:
        while test_cap.isOpened():
            ret, frame = test_cap.read()
            if not ret:
                print("Video khatam.")
                break
            
            cv2.imshow('Testing Feed for Integration', frame)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
                
        test_cap.release()
        cv2.destroyAllWindows()