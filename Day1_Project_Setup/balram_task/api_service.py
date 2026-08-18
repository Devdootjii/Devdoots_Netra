import requests
import threading
import os
from dotenv import load_dotenv

# .env se API URL load karna
load_dotenv()
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/alert")

def _send_request(payload):
    try:
        requests.post(BACKEND_API_URL, json=payload, timeout=1)
        print("✅ Alert sent successfully in background!")
    except requests.exceptions.RequestException:
        print("❌ Backend is offline. Alert logging failed (Background).")

def send_alert_async(payload):
    # API call ko alag background thread me bhejna taaki video freeze na ho
    thread = threading.Thread(target=_send_request, args=(payload,), daemon=True)
    thread.start()