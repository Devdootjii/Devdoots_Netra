import os
import time
import asyncio
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive']
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

# Configuration: Cooldown duration in seconds (1 alert per minute per camera)
ALERT_COOLDOWN_SECONDS = 60

# In-memory dictionary tracking the last alert timestamp for each camera ID
last_alert_tracker = {}

def is_camera_in_cooldown(camera_id: str) -> bool:
    """
    Checks if a camera is currently in cooldown period.
    Returns True if alert should be suppressed (blocked), False if alert is permitted.
    """
    current_time = time.time()
    last_dispatched = last_alert_tracker.get(camera_id, 0)
    
    elapsed_time = current_time - last_dispatched
    if elapsed_time < ALERT_COOLDOWN_SECONDS:
        remaining = int(ALERT_COOLDOWN_SECONDS - elapsed_time)
        print(f"[Cooldown Active] Alert suppressed for {camera_id}. Next allowed in {remaining}s.")
        return True
    
    return False

def record_alert_dispatch(camera_id: str):
    """Updates the last dispatched timestamp for the camera"""
    last_alert_tracker[camera_id] = time.time()

def upload_evidence_snapshot(image_path, camera_id):
    """Uploads snapshot to Drive with camera tagging"""
    if not os.path.exists(CREDS_FILE) or not os.path.exists(image_path):
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': f"Netra_RateLimited_{camera_id}_{os.path.basename(image_path)}"}
        media = MediaFileUpload(image_path, mimetype='image/jpeg', resumable=True)

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        permission = {'type': 'anyone', 'role': 'reader'}
        service.permissions().create(fileId=uploaded_file.get('id'), body=permission).execute()

        return uploaded_file.get('webViewLink')
    except Exception as e:
        print(f"[Drive Upload Warning]: {e}")
        return None

async def trigger_cooldown_safe_alert(camera_id: str, image_path: str, location_name: str = "Surveillance Zone"):
    """
    Day 5 Task 2 Entrypoint:
    Dispatches Telegram SOS alerts only if the camera is outside the cooldown window.
    """
    # 1. Check Cooldown Guard
    if is_camera_in_cooldown(camera_id):
        return {"status": "suppressed", "reason": "rate_limit_cooldown", "camera_id": camera_id}

    # 2. Upload snapshot evidence
    evidence_url = upload_evidence_snapshot(image_path, camera_id)
    if not evidence_url:
        evidence_url = "[Evidence Snapshot Upload Pending]"

    # 3. Formulate Telegram Notification Payload
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_text = (
        f"🚨 <b>PROJECT NETRA: RATE-LIMITED SOS ALERT</b> 🚨\n\n"
        f"📹 <b>Camera ID:</b> {camera_id}\n"
        f"📍 <b>Location:</b> {location_name}\n"
        f"⏰ <b>Timestamp:</b> {timestamp}\n"
        f"📸 <b>Evidence Link:</b> <a href='{evidence_url}'>View Snapshot</a>\n\n"
        f"🛡 <i>Anti-Spam Filter: Active ({ALERT_COOLDOWN_SECONDS}s cooldown per camera enforced).</i>"
    )

    # 4. Dispatch Telegram Notification
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print(f"[Simulated Dispatch Payload]:\n{alert_text}")
        record_alert_dispatch(camera_id)
        return {"status": "success", "mode": "simulated", "camera_id": camera_id}

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=alert_text, parse_mode="HTML")
        record_alert_dispatch(camera_id)
        print(f"[Alert Sent] Successfully dispatched SOS for {camera_id} at {timestamp}")
        return {"status": "success", "camera_id": camera_id}
    except Exception as e:
        print(f"[Telegram Dispatch Error]: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    print("Project Netra - Day 5 Task 2: Rate-Limit Cooldown Manager Ready.")