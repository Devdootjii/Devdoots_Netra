"""
NETRA Backend  —  FastAPI server.
Receives alerts + multi-camera status from the engine, serves live status to the
frontend, writes dynamic camera config, and powers a Gemini chatbot.

Run:  uvicorn main:app --reload   (from the backend/ folder)
"""
import json
import os
import time
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gemini_helper import get_client, generate

# Load .env from repo root (one level up from backend/)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

app = FastAPI(title="Project Netra Backend")

# CORS: allow the React frontend (Vite :5173 / :3000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The engine reads this file live — one source of truth for camera URLs.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(REPO_ROOT, ".runtime", "camera_config.json")

# Gemini API key for the chatbot (optional — bot still works with fallback responses).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
print("[NETRA BACKEND] GEMINI KEY:", "LOADED" if GEMINI_API_KEY else "NOT FOUND")
if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("AIzaSy"):
    print("[NETRA BACKEND] ⚠️  GEMINI_API_KEY doesn't look like a valid Gemini API key "
          "(valid keys start with 'AIzaSy'). Get one from https://aistudio.google.com/apikey")

# ---------------------------------------------------------------------------
# In-memory live state: the engine POSTs here every few seconds; the frontend
# GETs here every 2s. This is the bridge between them.
# ---------------------------------------------------------------------------
LIVE_STATE = {
    "camera_id": "Netra_Frontend_Stream",
    "location_name": "Dynamic Dashboard Camera",
    "threat_level": "NORMAL",
    "persons_detected": 0,
    "sos_active": False,
    "frame_timestamp": datetime.now().isoformat(),
    "status": "active",
    "message": "Awaiting engine data...",
}

# Rolling alert log (in-memory, survives for the process lifetime).
ALERT_LOG: list[dict] = []


# ----------------------------- Data models -----------------------------
class AlertData(BaseModel):
    camera: str
    threat: str


class MultiCamFrameData(BaseModel):
    camera_id: str
    location_name: str
    threat_level: str
    persons_detected: int
    sos_active: bool
    frame_timestamp: Optional[str] = None
    snapshot_b64: Optional[str] = None


class CameraUpdate(BaseModel):
    camera_1_url: str
    camera_2_url: str


class ChatMessage(BaseModel):
    message: str


# ----------------------------- Endpoints -----------------------------
@app.get("/health")
def health_check():
    return {"status": "success", "message": "Netra API is running perfectly."}


@app.post("/api/alert")
def receive_alert(data: AlertData):
    print(f"🚨 ALERT RECEIVED - Camera: {data.camera} | Threat: {data.threat}")
    return {"status": "success", "data_received": data}


@app.get("/api/status")
def camera_status():
    return {
        "camera_id": "Cam1",
        "status": "Active",
        "resolution": "1080p",
        "last_ping": "few seconds ago",
    }


def _write_log_to_file(camera_id: str, location_name: str, latency_ms: float):
    log_entry = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"Cam: {camera_id} ({location_name}) | Latency: {latency_ms:.2f} ms\n"
    )
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    log_path = os.path.join(os.path.dirname(CONFIG_PATH), "alert_latency_log.txt")
    with open(log_path, "a") as log_file:
        log_file.write(log_entry)


@app.post("/api/ai-stream")
async def receive_multicam_stream(data: MultiCamFrameData, background_tasks: BackgroundTasks):
    """Engine POSTs here. We store the data for the frontend to poll via GET."""
    global LIVE_STATE

    start_time = time.time()
    try:
        # Store the latest state for frontend polling.
        LIVE_STATE = {
            "camera_id": data.camera_id,
            "location_name": data.location_name,
            "threat_level": data.threat_level,
            "persons_detected": data.persons_detected,
            "sos_active": data.sos_active,
            "frame_timestamp": data.frame_timestamp or datetime.now().isoformat(),
            "status": "active",
            "message": "Stream active",
        }

        if data.sos_active or data.threat_level == "CRITICAL":
            latency_ms = (time.time() - start_time) * 1000
            print(
                f"🚨 [CRITICAL ALERT] Camera ID: {data.camera_id} | "
                f"Location: {data.location_name} | SOS Active"
            )
            # Add to alert log.
            ALERT_LOG.insert(0, {
                "id": int(time.time() * 1000),
                "type": "CRITICAL",
                "message": f"SOS Signal detected on {data.camera_id} ({data.location_name})",
                "time": datetime.now().strftime("%I:%M:%S %p"),
            })
            if len(ALERT_LOG) > 100:
                ALERT_LOG.pop()

            background_tasks.add_task(
                _write_log_to_file, data.camera_id, data.location_name, latency_ms
            )
            return {
                "status": "CRITICAL_PROCESSED",
                "camera_id": data.camera_id,
                "location": data.location_name,
                "latency_ms": latency_ms,
            }

        return {"status": "SUCCESS", "message": f"Data received from {data.camera_id}"}

    except Exception as er:
        print(f"❌ [SYSTEM ERROR] {str(er)}")
        raise HTTPException(status_code=400, detail="Bad Request: Async data processing failed.")


@app.get("/api/ai-stream")
def get_stream_status():
    """Frontend polls this every 2s — return the latest state from the engine."""
    return LIVE_STATE


@app.get("/api/alerts")
def get_alert_logs():
    """Return recent alert history."""
    return {"logs": ALERT_LOG, "count": len(ALERT_LOG)}


@app.post("/api/update-camera-urls")
async def update_camera_urls(data: CameraUpdate):
    """Writes the camera URLs the engine reads live."""
    try:
        config_data = {"cam_1": data.camera_1_url, "cam_2": data.camera_2_url}
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=4)
        print(f"✅ [CONFIG UPDATED] Cam 1: {data.camera_1_url} | Cam 2: {data.camera_2_url}")
        return {
            "status": "SUCCESS",
            "message": "Camera URLs updated successfully",
            "config": config_data,
        }
    except Exception as e:
        print(f"❌ [CONFIG ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to write config file.")


# ---------------------------------------------------------------------------
# Chatbot endpoint — Gemini-powered, context-aware with live system state.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are NETRA Assistant, an AI helper for the NETRA AI-powered
surveillance and emergency response system. You help users understand the current
system status, provide emergency guidance, and answer questions about the system.

Current system state you should reference:
- Persons detected: {persons}
- SOS active: {sos}
- Threat level: {threat}
- Camera: {camera}
- Last update: {timestamp}

Keep responses concise (2-3 sentences max). If someone seems to be in danger,
prioritize safety advice. You can explain how the system works, what the alerts mean,
or what actions to take."""


@app.post("/api/chat")
async def chat(data: ChatMessage):
    """Gemini-powered chatbot with live system context."""
    user_msg = data.message.strip()
    if not user_msg:
        return {"response": "Please type a message."}

    # Build context from current live state.
    context = SYSTEM_PROMPT.format(
        persons=LIVE_STATE.get("persons_detected", 0),
        sos=LIVE_STATE.get("sos_active", False),
        threat=LIVE_STATE.get("threat_level", "UNKNOWN"),
        camera=LIVE_STATE.get("camera_id", "Unknown"),
        timestamp=LIVE_STATE.get("frame_timestamp", "N/A"),
    )

    # Try Gemini if configured.
    if GEMINI_API_KEY:
        try:
            # FIX (Guide Fix 3): 'gemini-2.0-flash' is retired. gemini_helper
            # auto-discovers whichever flash model this key can currently
            # use, tries up to 5 candidates on a 404, and remembers whatever
            # worked so later requests skip straight to it.
            client = get_client(GEMINI_API_KEY)
            full_prompt = f"{context}\n\nUser question: {user_msg}"
            text, model_used, error = generate(client, full_prompt)
            if error:
                print(f"[CHAT] Gemini error: {error}")
                return {"response": _fallback_response(user_msg, LIVE_STATE)}
            return {"response": text}
        except Exception as e:
            print(f"[CHAT] Gemini error: {e}")
            return {"response": _fallback_response(user_msg, LIVE_STATE)}

    # Fallback: rule-based responses without Gemini.
    return {"response": _fallback_response(user_msg, LIVE_STATE)}


def _fallback_response(msg: str, state: dict) -> str:
    """Simple rule-based fallback when Gemini is not configured."""
    msg_lower = msg.lower()
    persons = state.get("persons_detected", 0)
    sos = state.get("sos_active", False)
    threat = state.get("threat_level", "NORMAL")

    if any(w in msg_lower for w in ["person", "people", "count", "how many"]):
        return f"Currently {persons} person(s) detected by the NETRA camera system."
    if any(w in msg_lower for w in ["sos", "emergency", "alert", "threat"]):
        if sos:
            return f"⚠️ SOS is ACTIVE! Threat level: {threat}. Emergency protocols should be followed immediately."
        return f"No active SOS. Threat level is {threat}. System is monitoring normally."
    if any(w in msg_lower for w in ["status", "system", "working", "online"]):
        return f"System is active. {persons} person(s) detected, threat level: {threat}, SOS: {'Active' if sos else 'Normal'}."
    if any(w in msg_lower for w in ["help", "what", "how"]):
        return "I'm the NETRA assistant. Ask me about detected persons, SOS status, threat levels, or emergency procedures. (Connect Gemini API for richer responses.)"
    return f"I received your message. System status: {persons} person(s), threat {threat}, SOS {'active' if sos else 'normal'}. (Connect Gemini API for AI-powered responses.)"