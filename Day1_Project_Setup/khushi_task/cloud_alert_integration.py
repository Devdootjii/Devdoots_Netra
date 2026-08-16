import os
import asyncio
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Bot

SCOPES = ['https://www.googleapis.com/auth/drive']

# Environment Variables (Secrets)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

def upload_to_drive(image_path):
    """Google Drive par snapshot upload karke public URL return karta hai"""
    if not os.path.exists(CREDS_FILE):
        print(f"[Drive] Error: {CREDS_FILE} not found.")
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
        print(f"[Drive] Upload Failed: {e}")
        return None

async def send_critical_alert(image_path, location="Camera Location 1"):
    """Drive Upload + Telegram Alert ko combine karke trigger karta hai"""
    print(f"\n[Alert Triggered] Processing threat alert for: {location}")
    
    # 1. Drive par snapshot upload karo
    image_url = upload_to_drive(image_path) if os.path.exists(image_path) else "Image not found"

    # 2. Telegram message create karo
    alert_message = (
        f"🚨 CRITICAL SOS ALERT 🚨\n"
        f"📍 Location: {location}\n"
        f"🖼 Snapshot Evidence: {image_url}\n"
        f"⚠️ Immediate action required!"
    )

    # 3. Telegram par bhej do
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print(f"[Telegram Ready] Formatted message:\n{alert_message}")
        return

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=alert_message)
        print("[Telegram] Alert sent successfully!")
    except Exception as e:
        print(f"[Telegram] Failed to send alert: {e}")

if __name__ == "__main__":
    print("Project Netra - Cloud & Alert Integration Module Ready.")