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