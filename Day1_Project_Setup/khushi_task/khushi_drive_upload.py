import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']

def upload_to_drive(image_path):
    creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    
    if not os.path.exists(creds_file):
        print(f"Error: {creds_file} not found. Please place credentials.json locally.")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(creds_file, scopes=SCOPES)
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

if __name__ == "__main__":
    print("Google Drive Upload Module Ready.")