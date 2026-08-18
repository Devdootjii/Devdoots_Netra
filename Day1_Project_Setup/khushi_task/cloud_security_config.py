import os

class CloudSecurityConfig:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

    @classmethod
    def validate_environment(cls):
        """Checks if critical secrets are properly configured via environment variables"""
        missing = []
        if not cls.BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")
        if not os.path.exists(cls.CREDS_FILE):
            missing.append(f"Credentials file ({cls.CREDS_FILE})")

        if missing:
            print(f"[Security Warning] Missing configs: {', '.join(missing)}")
            return False
        
        print("[Security Check] Environment variables validated successfully.")
        return True

if __name__ == "__main__":
    CloudSecurityConfig.validate_environment()