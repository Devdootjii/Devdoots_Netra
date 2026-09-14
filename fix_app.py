# fix_app.py — NETRA App.jsx fixer
# Run: python fix_app.py  (project root se, jahan frontend/ folder hai)
# Original App.jsx backup ho jayega App.jsx.bak mein

import os
import shutil

APP = os.path.join("frontend", "src", "App.jsx")
BAK = APP + ".bak"

if not os.path.exists(APP):
    print("ERROR: frontend/src/App.jsx nahi mila. Project root se run karo.")
    exit(1)

# Backup original
shutil.copy2(APP, BAK)
print("Backup saved:", BAK)

with open(APP, "r", encoding="utf-8") as f:
    lines = f.readlines()

s = "".join(lines)

# ============================================================
# 1. TEXT REPLACEMENTS (DroidCam -> Webcam/Engine)
# ============================================================
replacements = [
    # Constants
    ('const DROIDCAM_URL = "http://192.168.1.2:4747";',
     'const WEBCAM_LABEL = "Laptop Webcam (Device 0)";'),
    ('const DROIDCAM_VIDEO_URL = "http://192.168.1.2:4747/video";',
     'const WEBCAM_URL = "0";'),
    ('useState(DROIDCAM_VIDEO_URL)', 'useState(WEBCAM_URL)'),
    # Status messages
    ('"DroidCam ready. Click Connect Camera #1."',
     '"Webcam ready. Click Connect Camera to start."'),
    ('"Connecting to DroidCam Camera #1..."',
     '"Connecting to camera... (webcam default)"'),
    ('"DroidCam connection failed. Check phone IP, Wi-Fi and DroidCam app."',
     '"Camera connection failed. Make sure the engine (port 8001) is running."'),
    ('"DroidCam Camera #1 is LIVE."',
     '"Camera #1 is LIVE (webcam)."'),
    ('"DroidCam stream failed. Make sure http://192.168.1.2:4747 is reachable."',
     '"Camera stream failed. Make sure the engine (port 8001) is running."'),
    # JSX labels
    ("{DROIDCAM_URL}", "{WEBCAM_LABEL}"),
    ("192.168.1.2:4747", "127.0.0.1:8001"),
    ('"192.168.1.2"', '"127.0.0.1"'),
    ("Phone IP: 192.168.1.2", "Source: Webcam (Device 0)"),
    ("Port: 4747", "Port: 8001"),
    ("DROIDCAM CONNECTION", "NETRA ENGINE CONNECTION"),
    ("DROIDCAM SERVER", "ENGINE STREAM"),
    ("DroidCam Camera #1", "Camera #1 (Webcam)"),
    ("DroidCam #1", "NETRA Camera #1"),
    ("DroidCam Live Feed", "NETRA Live Feed"),
    ("DROIDCAM READY", "CAMERA READY"),
    ("Click Connect DroidCam", "Click Connect Camera"),
    ("CONNECTING DROIDCAM...", "CONNECTING CAMERA..."),
    ("DROIDCAM OFFLINE", "CAMERA OFFLINE"),
    ("Check phone Wi-Fi and DroidCam app.",
     "Make sure the engine is running on port 8001."),
    ("NETRA-DROIDCAM-01", "NETRA-CAM-01"),
    ("Connecting DroidCam...", "Connecting Camera..."),
    ("Reconnect DroidCam", "Reconnect Camera"),
    ('"Connect DroidCam"', '"Connect Camera"'),
    ('                      DroidCam\n', '                      Engine\n'),
    ('                      4747\n', '                      8001\n'),
    ('parsed.hostname === "192.168.1.2"', 'parsed.hostname === "127.0.0.1"'),
    ('parsed.port === "4747"', 'parsed.port === "8001"'),
    ("DroidCam integration for NETRA vision pipeline",
     "NETRA engine live camera with YOLOv8-pose detection"),
    ("DroidCam live camera with YOLO person and gender detection",
     "Webcam live camera with YOLOv8-pose person and SOS gesture detection"),
    ('placeholder="http://192.168.1.2:4747/video"',
     'placeholder="0 (webcam) or http://ip:port/video"'),
    ("<div>DroidCam</div>", "<div>Webcam</div>"),
]

count = 0
for old, new in replacements:
    if old in s:
        s = s.replace(old, new)
        count += 1
print(f"Text replacements applied: {count}/{len(replacements)}")

# ============================================================
# 2. GRID FIX: Move AI Processed Feed INSIDE the grid
# ============================================================
# Find "AI PROCESSED FEED" comment line
lines = s.split("\n")
ai_feed_idx = None
grid_close_idx = None  # the </div> that prematurely closes the grid
grid_open_idx = None

for i, line in enumerate(lines):
    if "AI PROCESSED FEED" in line and "comment" not in line.lower():
        ai_feed_idx = i
        break

if ai_feed_idx is None:
    print("ERROR: 'AI PROCESSED FEED' not found in App.jsx")
    exit(1)

# Find the grid opening line
for i in range(ai_feed_idx, 0, -1):
    if "grid grid-cols-1 md:grid-cols-2 gap-6 items-start" in lines[i]:
        grid_open_idx = i
        break

if grid_open_idx is None:
    print("ERROR: grid opening div not found")
    exit(1)

# Find the </div> between the last Camera stat box and the AI feed comment
# This is the grid's closing </div> that we need to move
# Search backwards from ai_feed_idx for a standalone </div> line
for i in range(ai_feed_idx - 1, grid_open_idx, -1):
    stripped = lines[i].strip()
    if stripped == "</div>":
        grid_close_idx = i
        # Check if the next non-empty line is the AI feed comment or nearby
        # We want the FIRST </div> we find going backwards from AI feed
        break

if grid_close_idx is None:
    print("ERROR: grid closing </div> not found between grid and AI feed")
    exit(1)

print(f"Grid opens at line {grid_open_idx + 1}")
print(f"Grid currently closes at line {grid_close_idx + 1}")
print(f"AI feed comment at line {ai_feed_idx + 1}")

# Remove the grid close line (and any empty line after it)
lines.pop(grid_close_idx)
# If the next line is empty, remove it too
if grid_close_idx < len(lines) and lines[grid_close_idx].strip() == "":
    lines.pop(grid_close_idx)
print("Removed premature grid close")

# Now find where to ADD the grid close: after the AI feed panel's last </div>
# The AI feed panel is inside the grid. Find where the outer container </div> is
# (the one that was the grid's parent — it comes after the AI feed panel)
# Look for the SETTINGS comment
settings_idx = None
for i, line in enumerate(lines):
    if "SETTINGS" in line and "comment" not in line.lower() and "{" in line:
        settings_idx = i
        break

if settings_idx is None:
    print("ERROR: SETTINGS section not found")
    exit(1)

# Find the </div> that closes the outer container (space-y-6 div)
# It's the last </div> before the )} that precedes SETTINGS
# Search backwards from settings_idx for the )} line, then find the </div> before it
close_paren_idx = None
for i in range(settings_idx - 1, ai_feed_idx, -1):
    if lines[i].strip() == ")}":
        close_paren_idx = i
        break

if close_paren_idx is None:
    print("ERROR: closing )} not found before SETTINGS")
    exit(1)

# The </div> just before )} closes the outer container
# We need to add our grid </div> BEFORE that one
# Find it
container_close_idx = None
for i in range(close_paren_idx - 1, ai_feed_idx, -1):
    if lines[i].strip() == "</div>":
        container_close_idx = i
        break

if container_close_idx is None:
    print("ERROR: container closing </div> not found")
    exit(1)

# Insert the grid </div> before the container close
# Get the indentation from the container close line
container_line = lines[container_close_idx]
indent = container_line[:len(container_line) - len(container_line.lstrip())]
lines.insert(container_close_idx, indent + "</div>")
lines.insert(container_close_idx, "")  # empty line for readability
print(f"Added grid close at line {container_close_idx + 1} (after AI feed panel)")

s = "\n".join(lines)

# ============================================================
# 3. Add NetraChatbot import and render
# ============================================================
if "import NetraChatbot" not in s:
    s = s.replace(
        'import React, { useEffect, useRef, useState } from "react";',
        'import React, { useEffect, useRef, useState } from "react";\nimport NetraChatbot from \'./NetraChatbot\';',
        1
    )
    print("Added NetraChatbot import")

if "<NetraChatbot" not in s:
    s = s.replace(
        '<div className="netra-footer"><NetraFooter /></div>',
        '<div className="netra-footer"><NetraFooter /></div>\n      <NetraChatbot />',
        1
    )
    print("Added NetraChatbot render")

# ============================================================
# Write result
# ============================================================
with open(APP, "w", encoding="utf-8") as f:
    f.write(s)

print("\n=== DONE ===")
print("App.jsx fixed. Original backup: App.jsx.bak")
print("Frontend ab 'npm run dev' se chalega.")
