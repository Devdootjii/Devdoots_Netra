# 👁️ NETRA

**See. Detect. Protect.** — An AI-Powered Intelligent Surveillance & Emergency Response System by Team Devdoots.

NETRA turns a passive camera feed into an active real-time threat & SOS detection engine. It watches a live video stream, counts people, recognizes sustained SOS distress gestures, and — when an emergency is confirmed — generates an AI forensic incident report (Gemini Vision) and archives the evidence to Google Drive.

---

## Architecture

NETRA runs as three processes:

```
┌─────────────────┐        status/alerts        ┌─────────────────┐
│  NETRA ENGINE    │ ─────────────────────────► │  BACKEND (API)   │
│  (port 8001)     │      POST /api/ai-stream   │  (port 8000)     │
│                  │                            │                  │
│  • webcam input  │                            │  • alert intake  │
│  • YOLOv8-pose   │◄────── camera_config ──────│  • latency log   │
│  • person count  │      (live hot-swap)       │  • config write  │
│  • 3-sec SOS     │                            └────────┬─────────┘
│  • Gemini report │                                     │
│  • Drive upload  │                                     │ alerts
│  • MJPEG feeds   │                                     ▼
└────────┬────────┘                            ┌─────────────────┐
         │  /live-feed  /live-feed-raw         │  FRONTEND (Vite) │
         └───────────────────────────────────► │  (port 5173)     │
                                                 │  React dashboard│
                                                 └─────────────────┘
```

**Pipeline:** frame capture (webcam) → YOLOv8-pose person detection → SOS gesture hold (3 s, anti-flicker) → backend alert + Gemini Vision forensic report → Google Drive evidence archive + dashboard alert.

The frontend also includes a **NETRA Assistant** chatbot (bottom-right floating widget) — a Gemini-powered, system-aware AI that can answer questions about current person counts, SOS status, threat levels, and emergency guidance.

## Repository Layout

```
netra/
├── engine/
│   └── netra_engine.py      # THE core: camera, vision, SOS, Gemini, Drive, MJPEG
├── backend/
│   ├── main.py              # FastAPI: alerts, status, camera config
│   ├── test_client.py       # manual test client
│   └── stress_test.py       # backend load test
├── frontend/                # React + Vite dashboard (Tailwind)
├── models/
│   └── yolov8n-pose.pt      # YOLOv8 nano pose weights
├── docs/                    # test & accuracy reports
├── assets/                  # screenshots and demo GIFs
├── camera_config.json       # camera source ("0" = laptop webcam)
├── requirements.txt
├── .env.example             # copy to .env, add your keys
└── start_netra.bat          # one-click launcher (Windows)
```

## Quick Start

### 1. Backend (Python 3.10+)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (source .venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
copy .env.example .env          # add GEMINI_API_KEY / Drive creds if you have them
cd backend
uvicorn main:app --reload
```

### 2. Engine (new terminal)

```bash
python engine\netra_engine.py
```

The engine opens the **laptop webcam** (device 0) by default. To use a network camera instead, edit `camera_config.json` — `cam_1` accepts an integer device index or a stream URL, and the engine hot-swaps without restarting.

### 3. Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dashboard tiles auto-connect to the engine feeds at http://127.0.0.1:8001/live-feed (AI overlay) and /live-feed-raw (clean camera).

Or on Windows, just run `start_netra.bat` to launch all three.

## How SOS Detection Works

1. **Person detection** — YOLOv8-pose at conf ≥ 0.5, tiny noise boxes (< 1% of frame) ignored.
2. **Gesture** — a wrist held above the shoulder (either arm) registers a distress cue; low-light keypoint confidence is gated at 0.30.
3. **Confirmation** — the gesture must hold for **3 seconds**; brief drops under 1.2 s are forgiven (anti-flicker).
4. **On confirm (edge-triggered, once per event):**
   - snapshot + status sent to the backend (`/api/ai-stream`),
   - **Gemini Vision** generates a structured forensic report (threat level, description, hazards, recommended action),
   - snapshot + report are uploaded to **Google Drive** as evidence.
5. A 15 s cooldown prevents duplicate evidence packs if the gesture re-triggers immediately.

> Gemini / Drive features are optional — if `GEMINI_API_KEY` or `GOOGLE_APPLICATION_CREDENTIALS` are not set, the engine logs a clear message and keeps running detection + alerting without them.

## Key Engine Endpoints

| Endpoint | Description |
|---|---|
| `GET /live-feed` | MJPEG stream with AI overlay (boxes, skeleton, SOS banner) |
| `GET /live-feed-raw` | MJPEG stream of the untouched camera frame |

## Key Backend Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | API health check |
| `POST /api/alert` | simple alert intake |
| `POST /api/ai-stream` | multi-camera status stream from the engine (with optional SOS snapshot) |
| `GET /api/ai-stream` | stream status |
| `POST /api/update-camera-urls` | update camera sources live (engine picks them up without restart) |
| `GET /api/alerts` | recent alert history (in-memory log) |
| `POST /api/chat` | Gemini-powered chatbot with live system context (person count, SOS, threat level) |

## Cloud Deployment (target)

- **Frontend** — Vercel / Netlify
- **Backend + Engine** — Docker container on Google Cloud Run
- **Secrets** — `.env` locally, GCP Secret Manager in production

## Team Devdoots

Built for the Code for Communities hackathon by Team Devdoots — every member understands and can explain every line of this system.
