import os
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Bot

SCOPES = ['https://www.googleapis.com/auth/drive']

# Configuration & Secrets
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "error_log.txt")

# Thread pool executor to offload blocking I/O (Drive Upload) without freezing camera FPS
executor = ThreadPoolExecutor(max_workers=3)

def log_error(module_name, error_message):
    """Async/Sync error logging with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{module_name}] {error_message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"[Logged Error] {log_entry.strip()}")
    except Exception as e:
        print(f"Logging Failed: {e}")

def _sync_drive_upload(image_path):
    """Synchronous worker function executed inside background thread pool"""
    if not os.path.exists(CREDS_FILE):
        log_error("Google Drive", f"Missing credentials: {CREDS_FILE}")
        return None

    if not os.path.exists(image_path):
        log_error("Google Drive", f"Evidence file not found: {image_path}")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': f"Netra_Async_{os.path.basename(image_path)}"}
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
        log_error("Google Drive Async", f"Drive upload error: {str(e)}")
        return None

async def async_upload_to_drive(image_path):
    """Non-blocking Drive upload wrapper to prevent video pipeline lag"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _sync_drive_upload, image_path)

async def dispatch_telegram_alert(image_url, location, timestamp):
    """Async non-blocking Telegram SOS alert dispatcher"""
    alert_text = (
        f"🚨 PROJECT NETRA: SOS ALERT (LATENCY OPTIMIZED) 🚨\n"
        f"⏰ Timestamp: {timestamp}\n"
        f"📍 Location: {location}\n"
        f"📸 Evidence Link: {image_url}\n"
        f"⚡ Status: Non-blocking background dispatch active!"
    )

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        log_error("Telegram Dispatcher", "Bot token missing.")
        return

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=alert_text)
        print(f"[Async Alert] Dispatched successfully for {location}")
    except Exception as e:
        log_error("Telegram Dispatcher", f"Async send failed: {str(e)}")

async def background_alert_task(image_path, location="Main Entrance Camera"):
    """
    FastAPI Background Task compatible entry point:
    Executes drive upload and telegram dispatch in the background
    without degrading real-time AI inference FPS.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Non-blocking Drive upload
    image_url = await async_upload_to_drive(image_path)
    if not image_url:
        image_url = "[Evidence Upload Failed - Logged Locally]"

    # 2. Async Telegram notification
    await dispatch_telegram_alert(image_url, location, timestamp)

if __name__ == "__main__":
    print("Project Netra - Day 4 Task 2: Async Cloud Pipeline Optimized.")