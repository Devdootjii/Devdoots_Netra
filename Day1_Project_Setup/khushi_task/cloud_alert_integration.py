import os
import asyncio
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from telegram import Bot

SCOPES = ['https://www.googleapis.com/auth/drive']

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHAT_ID = "YOUR_CHAT_ID_HERE"
CREDS_FILE = "credentials.json"

def upload_to_drive(image_path):
    if not os.path.exists(CREDS_FILE):
        print(f"Error: {CREDS_FILE} not found.")
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
        print(f"Upload Successful! Public URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"Failed to upload to Drive: {e}")
        return None

async def send_critical_alert(image_path, location="Camera Location 1"):
    image_url = upload_to_drive(image_path)
    if not image_url:
        image_url = "Image upload failed"

    alert_message = (
        f"🚨 CRITICAL SOS ALERT 🚨\n"
        f"📍 Location: {location}\n"
        f"🖼 Snapshot Evidence: {image_url}\n"
        f"⚠️ Immediate action required!"
    )

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=alert_message)
        print("Telegram alert sent successfully!")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

if __name__ == "__main__":
    print("Cloud & Telegram Alert Integration Script Ready.")
  


       

 

