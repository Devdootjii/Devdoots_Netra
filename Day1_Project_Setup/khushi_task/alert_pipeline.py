import os
import asyncio
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Bot

SCOPES = ['https://www.googleapis.com/auth/drive']

# Environment Variables & Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "error_log.txt")

def log_error(module_name, error_message):
    """Logs runtime exceptions to local error_log.txt with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{module_name}] {error_message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"[Logged] {log_entry.strip()}")
    except Exception as e:
        print(f"Logging Failed: {e}")

def upload_evidence_to_drive(image_path):
    """Uploads incident frame snapshot to Google Drive and returns public webViewLink"""
    if not os.path.exists(CREDS_FILE):
        log_error("Google Drive", f"Missing credentials file at: {CREDS_FILE}")
        return None

    if not os.path.exists(image_path):
        log_error("Google Drive", f"Image evidence not found at: {image_path}")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': f"Netra_Alert_{os.path.basename(image_path)}"}
        media = MediaFileUpload(image_path, mimetype='image/jpeg', resumable=True)

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        permission = {'type': 'anyone', 'role': 'reader'}
        service.permissions().create(fileId=uploaded_file.get('id'), body=permission).execute()

        public_url = uploaded_file.get('webViewLink')
        print(f"[Cloud Sync] Snapshot Uploaded: {public_url}")
        return public_url

    except Exception as e:
        log_error("Google Drive", f"Drive upload failure: {str(e)}")
        return None

async def trigger_threat_alert_pipeline(image_path, location="Main Entrance Camera"):
    """
    Main Alert Pipeline for Backend/AI integration:
    1. Uploads snapshot evidence to Google Drive.
    2. Dispatches real-time SOS alert with link to Telegram.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[PIPELINE TRIGGERED] SOS Event detected at {timestamp} | Location: {location}")

    # 1. Upload snapshot evidence
    evidence_url = upload_evidence_to_drive(image_path)
    if not evidence_url:
        evidence_url = "[Evidence Upload Failed - Logged Locally]"

    # 2. Construct SOS Alert payload
    alert_text = (
        f"🚨 PROJECT NETRA: CRITICAL SOS ALERT 🚨\n"
        f"⏰ Time: {timestamp}\n"
        f"📍 Location: {location}\n"
        f"📸 Evidence Link: {evidence_url}\n"
        f"⚠️ Status: Immediate Security Intervention Required!"
    )

    # 3. Dispatch to Telegram
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        log_error("Telegram Dispatcher", "Bot token missing in environment.")
        print(f"[Telegram Ready Payload]:\n{alert_text}")
        return {"status": "success", "evidence_url": evidence_url, "dispatched": False}

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=alert_text)
        print("[Telegram Dispatcher] Alert successfully dispatched!")
        return {"status": "success", "evidence_url": evidence_url, "dispatched": True}
    except Exception as e:
        log_error("Telegram Dispatcher", f"Failed sending message: {str(e)}")
        return {"status": "failed", "evidence_url": evidence_url, "error": str(e)}

if __name__ == "__main__":
    print("Project Netra - Day 4 Alert Pipeline Module Ready.")