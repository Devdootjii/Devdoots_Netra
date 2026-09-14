import threading
import requests

def send_alert(cam_id):
    url = "http://127.0.0.1:8000/api/ai-stream"
    data = {
        "camera_id": cam_id,
        "location_name": "Testing Zone",
        "threat_level": "CRITICAL",
        "persons_detected": 1,
        "sos_active": True
    }
    
    # API par POST request bhejna
    response = requests.post(url, json=data)
    print(f"[{cam_id}] Server Reply: {response.json()}")

# Ek sath 2 alag threads (Cameras) se request fire karna
print("Simulating 2 IP Cameras sending SOS at the exact same time...")
threading.Thread(target=send_alert, args=("Cam_01",)).start()
threading.Thread(target=send_alert, args=("Cam_02",)).start()