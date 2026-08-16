import os
import asyncio
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Bot

SCOPES = ['https://www.googleapis.com/auth/drive']

# Environment Variables (Secrets)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "error_log.txt")

def log_error(module_name, error_message):
    """Failures ko timestamp ke sath local error_log.txt mein append karta hai"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{module_name}] {error_message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"[Logged Error] {log_entry.strip()}")
    except Exception as e:
        print(f"Critical Logging Failure: {e}")

def upload_to_drive(image_path):
    """Google Drive upload with crash-proof logging"""
    if not os.path.exists(CREDS_FILE):
        log_error("Google Drive", f"Credentials file not found at: {CREDS_FILE}")
        return None

    if not os.path.exists(image_path):
        log_error("Google Drive", f"Image file not found at: {image_path}")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': os.path.basename(image_path)}
        media = MediaFileUpload(image_path, mimetype='image/jpeg', resumable=True)

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        permission = {'type': 'anyone', 'role': 'reader'}
        service.permissions().create(fileId=uploaded_file.get('id'), body=permission).execute()

        public_url = uploaded_file.get('webViewLink')
        print(f"[Drive] Upload Success: {public_url}")
        return public_url

    except Exception as e:
        log_error("Google Drive", f"Drive upload failed: {str(e)}")
        return None

async def send_critical_alert(image_path, location="Camera Location 1"):
    """Drive Upload + Telegram Alert with zero crash on network/rate-limit error"""
    print(f"\n[Alert Triggered] Processing threat alert for: {location}")
    
    # 1. Drive upload attempt with fallback
    image_url = upload_to_drive(image_path)
    if not image_url:
        image_url = "[Evidence Upload Failed - Logged to error_log.txt]"

    # 2. Telegram message payload
    alert_message = (
        f"🚨 CRITICAL SOS ALERT 🚨\n"
        f"📍 Location: {location}\n"
        f"🖼 Snapshot Evidence: {image_url}\n"
        f"⚠️ Immediate action required!"
    )

    # 3. Telegram dispatch with error handling
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        log_error("Telegram Alert", "Bot token not configured in environment.")
        return

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=alert_message)
        print("[Telegram] Alert sent successfully!")
    except Exception as e:
        log_error("Telegram Alert", f"Telegram alert delivery failed: {str(e)}")

if __name__ == "__main__":
    print("Project Netra - Stability & Error Logging Module Ready.")