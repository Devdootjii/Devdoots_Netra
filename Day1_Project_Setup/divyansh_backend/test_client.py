import requests
import json
from datetime import datetime

# Tumhare FastAPI server ka URL
API_URL = "http://127.0.0.1:8000/api/ai-stream"

# Dummy AI data jo Balram/Ritesh ka script generate karega
payload = {
    "camera_id": "Balram_Webcam",
    "threat_level": "CRITICAL",
    "persons_detected": 3,
    "sos_active": True,
    "frame_timestamp": datetime.now().isoformat()
}

print("Sending data to Netra Backend...")

# POST request bhejna
response = requests.post(API_URL, json=payload)

# Backend ka response check karna
if response.status_code == 200:
    print("✅ Success! Server Response:", response.json())
else:
    print("❌ Error:", response.status_code, response.text)