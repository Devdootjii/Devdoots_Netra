import time
import json
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# 1. APP INITIALIZATION
app = FastAPI(title="Project Netra - Unified Backend")

origins = ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# FIX: pehle CONFIG_PATH "../camera_config.json" tha - relative path, jo
# main.py aur netra_unified_engine.py ki folder-depth match hone par hi
# same file resolve karta tha. Thodi si bhi folder-structure mismatch (jaise
# engine ek extra subfolder me hona) aur dono alag-alag file padh/likh rahe
# hote - config sync silently fail ho jata. Ab dono files EXACT same absolute
# path use karte hain (user ke home folder me ek fixed jagah), taaki chahe
# jahan se bhi chalao, hamesha same file resolve ho.
NETRA_HOME = os.environ.get("NETRA_HOME", os.path.join(os.path.expanduser("~"), ".netra"))
os.makedirs(NETRA_HOME, exist_ok=True)
CONFIG_PATH = os.environ.get("NETRA_CONFIG_PATH", os.path.join(NETRA_HOME, "camera_config.json"))
print(f"[NETRA BACKEND] camera_config.json path -> {CONFIG_PATH}")

# 2. PYDANTIC MODELS (Strict Data Validation)
class AIStreamData(BaseModel):
    camera_id: str
    threat_level: str
    persons_detected: int
    sos_active: bool
    location_name: Optional[str] = "Unknown"
    frame_timestamp: Optional[str] = ""

class CameraUpdate(BaseModel):
    camera_1_url: str
    camera_2_url: str

# 3. IN-MEMORY STATE (Frontend ke liye data hold karega)
latest_ai_data = {
    "camera_id": "System_Init",
    "threat_level": "NORMAL",
    "persons_detected": 0,
    "sos_active": False,
    "location_name": "Unknown",
    "frame_timestamp": ""
}

# 4. BACKGROUND TASKS
def write_log_to_file(camera_id: str, location_name: str, latency_ms: float):
    log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cam: {camera_id} ({location_name}) | Latency: {latency_ms:.2f} ms\n"
    with open("alert_latency_log.txt", "a") as log_file:
        log_file.write(log_entry)

# 5. ENDPOINTS

@app.post("/api/update-camera-urls")
async def update_camera_urls(data: CameraUpdate):
    """
    FIX: netra_unified_engine.py reads keys "CAMERA_1_URL" / "CAMERA_2_URL" (uppercase).
    Previously this endpoint wrote "cam_1" / "cam_2" -> engine never found a match and
    silently fell back to local webcam index 0. We now write BOTH key styles so the
    engine always finds the URL, whatever version is running.
    """
    try:
        config_data = {
            "CAMERA_1_URL": data.camera_1_url,
            "CAMERA_2_URL": data.camera_2_url,
            # backward-compat aliases
            "cam_1": data.camera_1_url,
            "cam_2": data.camera_2_url,
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=4)
        print(f"[NETRA BACKEND] camera_config.json updated -> {config_data}")
        return {"status": "SUCCESS", "message": "Camera URLs updated successfully", "config": config_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to write config file.")

@app.get("/api/camera-config")
async def get_camera_config():
    """
    FIX: debug helper - lets you (or the frontend) confirm exactly what the
    engine is currently configured to read, from the browser or curl, without
    needing terminal/file access on the server.
    """
    if not os.path.exists(CONFIG_PATH):
        return {"exists": False, "path": CONFIG_PATH}
    try:
        with open(CONFIG_PATH, "r") as f:
            return {"exists": True, "path": CONFIG_PATH, "config": json.load(f)}
    except Exception:
        return {"exists": True, "path": CONFIG_PATH, "config": None, "error": "could not parse file"}

@app.post("/api/ai-stream")
async def receive_ai_data(data: AIStreamData, background_tasks: BackgroundTasks):
    global latest_ai_data
    start_time = time.time()

    # State Update
    latest_ai_data.update(data.dict())

    # Alert Logic & Background Logging
    if data.sos_active or data.threat_level == "CRITICAL":
        print(f"[CRITICAL ALERT] Camera: {data.camera_id} | SOS Active. Triggering Telegram Alert...")
        latency_ms = (time.time() - start_time) * 1000
        background_tasks.add_task(write_log_to_file, data.camera_id, data.location_name, latency_ms)

    return {"status": "success", "message": "AI Data Synced to Backend"}

@app.get("/api/ai-stream")
async def send_ai_data_to_frontend():
    return latest_ai_data