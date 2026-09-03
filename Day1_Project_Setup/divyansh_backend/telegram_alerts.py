

import os
import time
import base64
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "60"))

SCOPES = ["https://www.googleapis.com/auth/drive"]

_executor = ThreadPoolExecutor(max_workers=2)
_last_alert_at = {}  # camera_id -> unix timestamp (in-memory cooldown tracker)


def _is_configured() -> bool:
    return bool(BOT_TOKEN) and bool(CHAT_ID)


def _in_cooldown(camera_id: str) -> bool:
    last = _last_alert_at.get(camera_id, 0)
    return (time.time() - last) < ALERT_COOLDOWN_SECONDS


def _save_snapshot_jpg(snapshot_b64: Optional[str]) -> Optional[str]:
    """Decode the base64 JPEG the engine sent and write it to a temp file so
    it can be attached to the Telegram message / uploaded to Drive."""
    if not snapshot_b64:
        return None
    try:
        netra_home = os.environ.get("NETRA_HOME", os.path.join(os.path.expanduser("~"), ".netra"))
        snap_dir = os.path.join(netra_home, "snapshots")
        os.makedirs(snap_dir, exist_ok=True)
        path = os.path.join(snap_dir, f"sos_{int(time.time())}.jpg")
        with open(path, "wb") as f:
            f.write(base64.b64decode(snapshot_b64))
        return path
    except Exception as e:
        print(f"[NETRA ALERTS] Failed to save snapshot: {e}")
        return None


def _upload_to_drive(image_path: Optional[str]) -> Optional[str]:
    if not DRIVE_AVAILABLE or not image_path or not os.path.exists(image_path):
        return None
    if not os.path.exists(CREDS_FILE):
        return None  # Drive is optional - just skip quietly
    try:
        creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        service = build("drive", "v3", credentials=creds)
        file_metadata = {"name": f"Netra_SOS_{os.path.basename(image_path)}"}
        media = MediaFileUpload(image_path, mimetype="image/jpeg", resumable=True)
        uploaded = service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
        service.permissions().create(fileId=uploaded.get("id"), body={"type": "anyone", "role": "reader"}).execute()
        return uploaded.get("webViewLink")
    except Exception as e:
        print(f"[NETRA ALERTS] Drive upload failed (continuing without it): {e}")
        return None


async def send_sos_alert(camera_id: str, location_name: str, snapshot_b64: Optional[str] = None):
    """
    Main entrypoint. Call as a FastAPI background task on every SOS-active
    payload - cooldown is handled internally, so duplicate calls within
    ALERT_COOLDOWN_SECONDS are silently suppressed (not an error).
    """
    if not _is_configured():
        print(
            "[NETRA ALERTS] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set - "
            "skipping alert. Fill these into your .env file."
        )
        return {"status": "skipped", "reason": "not_configured"}

    if _in_cooldown(camera_id):
        return {"status": "suppressed", "reason": "cooldown"}

    _last_alert_at[camera_id] = time.time()  # mark immediately, before any awaits

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    loop = asyncio.get_running_loop()

    snapshot_path = await loop.run_in_executor(_executor, _save_snapshot_jpg, snapshot_b64)
    evidence_url = await loop.run_in_executor(_executor, _upload_to_drive, snapshot_path)

    caption = (
        f"🚨 <b>PROJECT NETRA: SOS ALERT</b> 🚨\n\n"
        f"📹 <b>Camera:</b> {camera_id}\n"
        f"📍 <b>Location:</b> {location_name}\n"
        f"⏰ <b>Time:</b> {timestamp}\n"
        + (f"📸 <b>Drive backup:</b> <a href='{evidence_url}'>View</a>\n" if evidence_url else "")
    )

    try:
        bot = Bot(token=BOT_TOKEN)
        if snapshot_path and os.path.exists(snapshot_path):
            with open(snapshot_path, "rb") as photo:
                await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(chat_id=CHAT_ID, text=caption, parse_mode=ParseMode.HTML)
        print(f"[NETRA ALERTS] SOS alert sent for {camera_id} at {timestamp}")
        return {"status": "sent"}
    except Exception as e:
        print(f"[NETRA ALERTS] Telegram send failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    print("Project Netra - consolidated SOS alert module.")
    print(f"Configured: {_is_configured()}  |  Drive available: {DRIVE_AVAILABLE}")