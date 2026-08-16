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