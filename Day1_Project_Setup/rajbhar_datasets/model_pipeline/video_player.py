import cv2

# Yahan apni video ka pura rasta (path) daalein jahan abnormal video rakhi hai
# Example: "C:/Users/atulkumar/OneDrive/Pictures/rajbhar_datasets/Devdoots_Netra/Day2_Project_Setup/rajbhar_videos/abnormal_videos/video1.mp4"
video_path = r"C:\Users\atulkumar\Downloads\sos_video.mp4.mp4"

# Video ko read karna
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: Video '{video_path}' nahi khul rahi hai. Kripya file ka naam aur rasta check karein.")
else:
    print("Video start ho gayi hai. Playback band karne ke liye 'q' dabayein.")

# Frame-by-frame play karna
while cap.isOpened():
    ret, frame = cap.read()
    
    # Agar frames khatam ho jayein toh loop rok do
    if not ret:
        print("Video poori khatam ho gayi.")
        break
        
    # Frame ko screen par display karna
    cv2.imshow('Model Feed Pipeline - Frame by Frame', frame)
    
    # 25ms ka delay, aur 'q' dabane par window band ho jayegi
    if cv2.waitKey(25) & 0xFF == ord('q'):
        print("User ne video band kar di.")
        break

# Memory aur windows clear karna
cap.release()
cv2.destroyAllWindows()