import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# .env file load karna
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key or "your_gemini" in api_key:
    print("❌ Error: .env file mein asli GEMINI_API_KEY daaliye!")
else:
    print("🔑 API Key mil gayi! Gemini connect ho raha hai...")
    
    # Client initialize
    client = genai.Client(api_key=api_key)
    
    # Forensic Report Prompt
    prompt = """
    You are an emergency CCTV surveillance forensic engine.
    Generate a concise structured incident report for an emergency alert:
    1. Threat Level (High/Critical)
    2. Visual Description of the distress event
    3. Immediate Hazards
    4. Action Recommended
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        print("\n✅ Gemini Connected Successfully!")
        print("📄 Sample Generated Forensic Report:\n")
        print(response.text)
    except Exception as e:
        print(f"❌ Error aaya: {e}")