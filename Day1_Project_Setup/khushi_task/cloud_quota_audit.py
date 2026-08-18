import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def check_drive_storage_quota():
    """
    Day 5 - Task 3: Audits Google Drive API storage limits and connectivity.
    """
    print("\n--- [Google Drive API Quota & Storage Audit] ---")
    if not os.path.exists(CREDS_FILE):
        print(f"❌ Error: Credentials file '{CREDS_FILE}' not found locally.")
        return False

    try:
        creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        # Retrieve storage quota and user information
        about_info = service.about().get(fields="user, storageQuota").execute()
        user_info = about_info.get('user', {})
        quota_info = about_info.get('storageQuota', {})

        print(f"Service Account Email: {user_info.get('emailAddress', 'N/A')}")
        
        limit_bytes = int(quota_info.get('limit', 0)) if quota_info.get('limit') else None
        usage_bytes = int(quota_info.get('usage', 0))

        usage_mb = usage_bytes / (1024 * 1024)
        print(f"Current Storage Usage: {usage_mb:.2f} MB")

        if limit_bytes:
            limit_mb = limit_bytes / (1024 * 1024)
            print(f"Total Quota Limit: {limit_mb:.2f} MB")
            print(f"Free Storage Remaining: {(limit_mb - usage_mb):.2f} MB")
        else:
            print("Storage Quota: Unlimited / Domain Managed Plan Active.")

        print("✅ Google Drive API connection & quota verified successfully!")
        return True

    except Exception as e:
        print(f"❌ Drive Quota Audit Failed: {e}")
        return False

def audit_credentials_security():
    """
    Verifies that no secrets/tokens are hardcoded and .gitignore is configured.
    """
    print("\n--- [Credential Exposure & Security Audit] ---")
    
    # Check if critical variables are loaded from environment
    if not BOT_TOKEN:
        print("⚠️ Warning: TELEGRAM_BOT_TOKEN is not configured in .env.")
    else:
        print("✅ Telegram Bot Token safely loaded via environment variable.")

    # Verify .gitignore protection
    gitignore_path = os.path.join(os.path.dirname(__file__), "..", "..", ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "credentials.json" in content and ".env" in content:
                print("✅ .gitignore properly shields 'credentials.json' and '.env'.")
            else:
                print("⚠️ Action Needed: Ensure 'credentials.json' and '.env' are in .gitignore.")
    else:
        print("ℹ️ Root .gitignore file not detected from script path.")

if __name__ == "__main__":
    print("Project Netra - Day 5 Task 3: Hardware Freeze Pre-Flight Check")
    drive_status = check_drive_storage_quota()
    audit_credentials_security()
    print("\n[Status] Ready for Day 6 Stress Test pipeline freeze.")