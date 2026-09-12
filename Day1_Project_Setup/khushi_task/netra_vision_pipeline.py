import os
import datetime
from PIL import Image
from dotenv import load_dotenv
from google import genai
from khushi_drive_upload import upload_evidence, upload_report_text

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def process_threat_incident(image_path: str):
    """
    1. Threat frame ka Gemini Vision se Forensic Analysis karta hai.
    2. Incident image aur Forensic Report dono ko Google Drive par archive karta hai.
    """
    if not os.path.exists(image_path):
        return {"status": "error", "message": "Image not found"}

    print(f"🚨 Threat detected! Processing frame: {image_path}...")

    # 1. Gemini Vision Analysis
    image = Image.open(image_path)
    prompt = """
    You are an emergency CCTV surveillance forensic engine.
    Analyze this threat frame and generate an automated structured incident report:
    - Threat Level: [High / Critical]
    - Incident Description: [Concise summary of physical cues/distress/hazard]
    - Key Observations: [Persons detected, objects, posture]
    - Immediate Action Required: [Dispatch/Containment steps]
    Keep it strictly factual, professional, and under 150 words.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[image, prompt]
        )
        report_text = response.text
    except Exception as e:
        report_text = f"Gemini Forensic Analysis failed: {str(e)}"

    # 2. Upload to Google Drive (Evidence Archiving)
    print("☁️ Archiving evidence to Google Drive...")
    uploaded_image = upload_evidence(image_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    uploaded_report = upload_report_text(report_text, report_name=f"Forensic_Report_{timestamp}.txt")

    result = {
        "status": "success",
        "timestamp": timestamp,
        "forensic_report": report_text,
        "image_drive_link": uploaded_image.get("webViewLink") if uploaded_image else "Drive upload failed",
        "report_drive_link": uploaded_report.get("webViewLink") if uploaded_report else "Report upload failed"
    }

    return result

if __name__ == "__main__":
    print("✅ Netra Vision & Archiving Pipeline is ready for integration!")