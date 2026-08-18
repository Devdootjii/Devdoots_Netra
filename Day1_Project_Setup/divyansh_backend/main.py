from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Project Netra Backend")

# API Data Structure define karna
class AlertData(BaseModel):
    camera: str
    threat: str

@app.get("/health")
def health_check():
    return {"status": "success", "message": "Netra API is running perfectly."}

# Task 2: Naya POST Endpoint
@app.post("/api/alert")
def receive_alert(data: AlertData):
    # Data ko console mein print karna (Goal ke hisaab se)
    print(f"🚨 ALERT RECEIVED - Camera: {data.camera} | Threat: {data.threat}")
    return {"status": "success", "data_received": data}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Project Netra Backend")

# Step 1: CORS Configuration lagana
# React frontend by default port 5173 (Vite) ya 3000 par chalta hai
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Sirf in URLs ko humari API hit karne ki permission hogi
    allow_credentials=True,
    allow_methods=["*"], # GET, POST, sabhi requests allow hongi
    allow_headers=["*"],
)

# Day 1 ka code
class AlertData(BaseModel):
    camera: str
    threat: str

@app.get("/health")
def health_check():
    return {"status": "success", "message": "Netra API is running perfectly."}

@app.post("/api/alert")
def receive_alert(data: AlertData):
    print(f"🚨 ALERT RECEIVED - Camera: {data.camera} | Threat: {data.threat}")
    return {"status": "success", "data_received": data}

# Step 2: Day 2 Ka Naya GET Endpoint
@app.get("/api/status")
def camera_status():
    # Frontend ko dummy camera data return karne ke liye
    return {
        "camera_id": "Cam1",
        "status": "Active",
        "resolution": "1080p",
        "last_ping": "few seconds ago"
    }
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Project Netra Backend")

origins = ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class AIFrameData(BaseModel):
    camera_id: str
    threat_level: str
    persons_detected: int
    sos_active: bool
    frame_timestamp: Optional[str] = None

# Day 4 Task 2: Logging Function
def log_alert_metric(camera_id: str, latency_ms: float):
    log_filename = "alert_latency_log.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{current_time}] Camera: {camera_id} | Total Processing Latency: {latency_ms:.2f} ms\n"
    
    with open(log_filename, "a") as log_file:
        log_file.write(log_entry)

@app.post("/api/ai-stream")
def receive_ai_stream(data: AIFrameData):
    start_time = time.time()
    try:
        if data.sos_active or data.threat_level == "CRITICAL":
            print(f"🚨 [CRITICAL ALERT] Camera: {data.camera_id} | SOS Active")
            
            # Latency calculate karna
            latency_ms = (time.time() - start_time) * 1000
            
            # Log file mein data record karna
            log_alert_metric(data.camera_id, latency_ms)
            
            print(f"⚡ System Latency & Logged: {latency_ms:.2f} ms")
            
            return {
                "status": "CRITICAL_PROCESSED", 
                "action": "Cloud & UI Sync Triggered",
                "latency_ms": latency_ms
            }
        
        print(f"✅ [NORMAL] Camera: {data.camera_id} | Persons: {data.persons_detected}")
        return {"status": "SUCCESS", "message": "Frame data received"}

    except Exception as er:
        print(f"❌ [SYSTEM ERROR] {str(er)}")
        raise HTTPException(status_code=400, detail="Bad Request: Data processing failed.")
# Naya GET route taaki frontend connection check karte waqt crash na ho
@app.get("/api/ai-stream")
def get_ai_stream_status():
    return {
        "status": "active",
        "message": "AI Stream endpoint is ready to receive POST data."
    }