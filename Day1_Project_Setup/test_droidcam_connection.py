"""
Standalone test - engine load kiye bina, sirf ye check karta hai ki Python
(requests library) DroidCam URL tak pahunch pa raha hai ya nahi, aur agar
nahi to EXACT reason kya hai.

Run: python test_droidcam_connection.py
"""
import requests

URL = "http://100.124.45.6:4747/video"  # apna current DroidCam URL yahan daalo

print(f"Trying to connect to: {URL}\n")

try:
    resp = requests.get(URL, stream=True, timeout=5)
    print(f"Connected! HTTP status: {resp.status_code}")
    content_type = resp.headers.get('Content-Type', '')
    print(f"Content-Type: {content_type}")

    if "multipart" not in content_type and "video" not in content_type and "image" not in content_type:
        print("\n⚠️  This does NOT look like a video stream response.")
        print("Printing the actual response body so we can see what it is:\n")
        print("-" * 60)
        print(resp.text[:2000])
        print("-" * 60)
    else:
        print("\nTrying to read first chunk of data...")
        chunk = next(resp.iter_content(chunk_size=2048))
        print(f"Got {len(chunk)} bytes. Stream is readable.")
    resp.close()

except requests.exceptions.ConnectTimeout:
    print("FAILED: Connection TIMED OUT.")
    print("-> Engine machine cannot reach this host at all within 5s.")
    print("-> Check: is Tailscale running & connected on THIS machine (the one running the engine)?")
except requests.exceptions.ConnectionError as e:
    print(f"FAILED: Connection refused/error -> {e}")
    print("-> Either DroidCam app isn't running/listening, or host is unreachable from this machine.")
except requests.exceptions.ReadTimeout:
    print("FAILED: Connected, but no data received in time (read timeout).")
    print("-> DroidCam app may be open but not actively streaming.")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")