import os
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

# Predefined Camera Location Map for Multi-Camera Setup
CAMERA_METADATA = {
    "CAM_01": {"name": "IP Cam 1", "location": "Main Entrance Gate"},
    "CAM_02": {"name": "IP Cam 2", "location": "Corridor / Parking Block"},
    "CAM_DEFAULT": {"name": "Unknown Camera", "location": "Campus Surveillance Zone"}
}

def upload_evidence_snapshot(image_path, camera_id="CAM_01"):
    """Uploads snapshot to Drive with dynamic camera tagging"""
    if not os.path.exists(CREDS_FILE) or not os.path.exists(image_path):
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': f"Netra_Alert_{camera_id}_{os.path.basename(image_path)}"}
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
        print(f"[Drive Upload Error]: {e}")
        return None

async def send_dynamic_camera_alert(camera_id, image_path, custom_location=None):
    """
    Day 5 Task 1: Sends dynamic SOS alerts with real-time Camera ID and Location mapping
    """
    cam_info = CAMERA_METADATA.get(camera_id, CAMERA_METADATA["CAM_DEFAULT"])
    location_name = custom_location if custom_location else cam_info["location"]
    cam_name = cam_info["name"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Step 1: Upload snapshot evidence
    evidence_url = upload_evidence_snapshot(image_path, camera_id)
    if not evidence_url:
        evidence_url = "[Visual snapshot upload failed or pending]"

    # Step 2: Formulate dynamic Telegram SOS message
    alert_text = (
        f"🚨 <b>PROJECT NETRA: CRITICAL SOS DETECTED</b> 🚨\n\n"
        f"📹 <b>Camera ID:</b> {camera_id} ({cam_name})\n"
        f"📍 <b>Location:</b> {location_name}\n"
        f"⏰ <b>Timestamp:</b> {timestamp}\n"
        f"📸 <b>Evidence Link:</b> <a href='{evidence_url}'>View Snapshot</a>\n\n"
        f"⚡ <i>Action: Multi-Camera hardware stream triggered automatic dispatch.</i>"
    )

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print(f"[Simulated Alert Payload]:\n{alert_text}")
        return

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=alert_text, parse_mode="HTML")
        print(f"[Alert Dispatched] Threat notification sent for {camera_id} at {location_name}")
    except Exception as e:
        print(f"[Telegram Alert Dispatch Failed]: {e}")

if __name__ == "__main__":
    print("Project Netra - Day 5 Task 1: Dynamic Multi-Camera Alert Pipeline Loaded.")