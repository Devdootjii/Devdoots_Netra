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
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Project Netra - Multi-Camera Backend (Async)")

origins = ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class MultiCamFrameData(BaseModel):
    camera_id: str
    location_name: str
    threat_level: str
    persons_detected: int
    sos_active: bool
    frame_timestamp: Optional[str] = None

# Day 5 Task 2: Background logging function (I/O operation)
def write_log_to_file(camera_id: str, location_name: str, latency_ms: float):
    log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cam: {camera_id} ({location_name}) | Latency: {latency_ms:.2f} ms\n"
    with open("alert_latency_log.txt", "a") as log_file:
        log_file.write(log_entry)

# Day 5 Task 2: Using BackgroundTasks & async def to prevent blocking
@app.post("/api/ai-stream")
async def receive_multicam_stream(data: MultiCamFrameData, background_tasks: BackgroundTasks):
    start_time = time.time()
    try:
        if data.sos_active or data.threat_level == "CRITICAL":
            print(f"🚨 [CRITICAL ALERT] Camera ID: {data.camera_id} | Location: {data.location_name} | SOS Active")
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Blocking task (file writing) ko background worker ko de diya
            background_tasks.add_task(write_log_to_file, data.camera_id, data.location_name, latency_ms)
            
            return {
                "status": "CRITICAL_PROCESSED", 
                "camera_id": data.camera_id,
                "location": data.location_name,
                "latency_ms": latency_ms
            }
        
        print(f"✅ [NORMAL] Camera: {data.camera_id} ({data.location_name}) | Persons: {data.persons_detected}")
        return {"status": "SUCCESS", "message": f"Data received from {data.camera_id}"}

    except Exception as er:
        print(f"❌ [SYSTEM ERROR] {str(er)}")
        raise HTTPException(status_code=400, detail="Bad Request: Async data processing failed.")

@app.get("/api/ai-stream")
def get_stream_status():
    return {"status": "active", "message": "Async Multi-Camera backend listening."}

import json
import os
from pydantic import BaseModel

# Naya model incoming URLs receive karne ke liye
class CameraUpdate(BaseModel):
    camera_1_url: str
    camera_2_url: str

# Day 6 Task: Dynamic Camera Config Updater
@app.post("/api/update-camera-urls")
async def update_camera_urls(data: CameraUpdate):
    try:
        config_data = {
            "cam_1": data.camera_1_url,
            "cam_2": data.camera_2_url
        }
        
        # Root directory (Day1_Project_Setup) me JSON file save karna
        # Assumes main.py is inside divyansh_backend folder
        config_path = os.path.join(os.path.dirname(__file__), "..", "camera_config.json")
        
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=4)
            
        print(f"✅ [CONFIG UPDATED] Cam 1: {data.camera_1_url} | Cam 2: {data.camera_2_url}")
        
        return {
            "status": "SUCCESS", 
            "message": "Camera URLs updated successfully", 
            "config": config_data
        }
        
    except Exception as e:
        print(f"❌ [CONFIG ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to write config file.")