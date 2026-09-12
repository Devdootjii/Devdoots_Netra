import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaInMemoryUpload

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    if not os.path.exists(creds_file):
        # Agar khushi_task ke folder me credentials.json hai
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_creds = os.path.join(current_dir, "credentials.json")
        if os.path.exists(local_creds):
            creds_file = local_creds
        else:
            print(f"❌ Error: {creds_file} not found locally.")
            return None

    credentials = service_account.Credentials.from_service_account_file(
        creds_file, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=credentials)

def upload_evidence(file_path: str, mime_type: str = "image/jpeg"):
    """Snapshot image ko Google Drive par upload karta hai"""
    service = get_drive_service()
    if not service or not os.path.exists(file_path):
        return None

    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype=mime_type)
    
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink, webContentLink'
    ).execute()
    
    return uploaded_file

def upload_report_text(report_content: str, report_name: str = "forensic_report.txt"):
    """Gemini ki banayi Forensic Report ko Google Drive par log karta hai"""
    service = get_drive_service()
    if not service:
        return None

    file_metadata = {'name': report_name, 'mimeType': 'text/plain'}
    media = MediaInMemoryUpload(report_content.encode('utf-8'), mimetype='text/plain')

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    return uploaded_file