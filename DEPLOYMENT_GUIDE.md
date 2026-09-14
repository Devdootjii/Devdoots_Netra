# NETRA — Deployment Guide (Step by Step)

```
ARCHITECTURE (Deployed):

  ┌──────────────┐        HTTPS         ┌──────────────────┐
  │  Vercel       │ ──────────────────► │  Render            │
  │  Frontend     │   /api/chat          │  Backend (Docker) │
  │  (React)      │   /api/ai-stream     │  port 8000         │
  │  port 443     │ ◄──────────────────  │                    │
  └──────┬───────┘                      └──────────────────┘
         │
         │  MJPEG stream (HTTPS via tunnel)
         ▼
  ┌──────────────────┐
  │  YOUR LAPTOP      │
  │  Engine (Python)  │  ← webcam (device 0)
  │  port 8001        │
  │  Cloudflare Tunnel│  → https://xxx.trycloudflare.com
  └──────────────────┘
```

## Why this architecture?

- **Frontend** on Vercel: free, fast CDN, GitHub se auto-deploy
- **Backend** on Render: free Docker hosting, always-on
- **Engine** on your laptop: it NEEDS webcam — cloud pe webcam nahi hoti.
  Cloudflare Tunnel se laptop ka engine internet pe expose hota hai
  (free, koi port forwarding nahi chahiye)

---

## STEP 0: GitHub pe code push karo

Sabse pehle apna clean NETRA repo GitHub pe push karo:

```bash
cd Netra
git init
git add .
git commit -m "NETRA — clean restructured repo"
git remote add origin https://github.com/Devdootjii/Devdoots_Netra.git
git push -u origin main
```

Isse Vercel aur Render dono GitHub se code utha sakenge.

---

## STEP 1: Frontend → Vercel deploy

### 1.1 Vercel pe account banao
- https://vercel.com par jao
- "Sign Up" → GitHub se login karo
- Vercel tumhara GitHub access le lega

### 1.2 Project import karo
- Dashboard → "Add New Project"
- "Import Git Repository" → apna Devdoots_Netra repo select karo
- **Root Directory**: `frontend` set karo (IMPORTANT — repo root nahi, frontend folder)
- **Framework Preset**: Vite (auto-detect hoga)
- **Build Command**: `npm run build` (already set)
- **Output Directory**: `dist` (already set)

### 1.3 Environment Variables set karo
Vercel settings mein Environment Variables add karo:

| Name | Value |
|------|-------|
| `VITE_BACKEND_URL` | (STEP 2 ke baad milega — abhi skip karo) |
| `VITE_ENGINE_URL` | (STEP 3 ke baad milega — abhi skip karo) |

### 1.4 Deploy!
- "Deploy" button dabao
- 2-3 minute mein deploy ho jayega
- URL milega: `https://devdoots-netra.vercel.app`
- Environment Variables baad mein update kar sakte ho (Settings → Environment Variables)

### 1.5 IMPORTANT — App.jsx mein env var support
App.jsx mein ye 2 lines dhundo (approx line 12-13):

```javascript
// CURRENT (hardcoded — local only):
const BACKEND_BASE = "http://127.0.0.1:8000";
const AI_ENGINE_BASE = "http://127.0.0.1:8001";

// REPLACE WITH (env var with fallback):
const BACKEND_BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
const AI_ENGINE_BASE = import.meta.env.VITE_ENGINE_URL || "http://127.0.0.1:8001";
```

Isse local dev mein `127.0.0.1` use hoga, production mein Vercel ke env vars use honge.

---

## STEP 2: Backend → Render deploy (Docker seekhna!)

### 2.1 Render pe account banao
- https://render.com par jao
- "Get Started" → GitHub se sign up
- Email verify karo

### 2.2 New Web Service banao
- Dashboard → "New +" → "Web Service"
- GitHub repo select karo (Devdoots_Netra)
- Settings:
  - **Name**: `netra-backend`
  - **Runtime**: Docker (ye select karo — Docker seekh rahe ho!)
  - **Dockerfile Path**: `./backend/Dockerfile`
  - **Plan**: Free

### 2.3 Docker kya karta hai? (Learning)
Jab Render pe "Create" dabate ho, ye hota hai:

1. Render ek Linux server (container) start karta hai
2. `Dockerfile` ke instructions step-by-step follow karta hai:
   - `FROM python:3.12-slim` → Python 3.12 ka clean Linux image download
   - `RUN apt-get install...` → OpenCV ke liye system libs install
   - `COPY requirements.txt` → tumhari requirements copy
   - `RUN pip install torch...` → CPU torch install (2 min lagta hai)
   - `RUN pip install -r requirements.txt` → baaki sab
   - `COPY . .` → backend ka code copy
   - `CMD uvicorn main:app...` → server start
3. Container ready ho jaata hai, Render usse internet pe expose karta hai

### 2.4 Environment Variables
Render ke "Environment" tab mein:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | `AIzaSy_tumhari_gemini_key` |

### 2.5 Deploy!
- "Create Web Service" dabao
- 5-10 minute lagenge (Docker image build hota hai, torch install hota hai)
- URL milega: `https://netra-backend.onrender.com`
- Test: browser mein `https://netra-backend.onrender.com/health` kholo
- Agar `{"status":"success"...}` aaye toh backend live hai!

### 2.6 Vercel mein Backend URL update karo
Vercel → Settings → Environment Variables:
- `VITE_BACKEND_URL` = `https://netra-backend.onrender.com`
- Redeploy karo (Deployments → Redeploy)

---

## STEP 3: Engine → Local laptop + Cloudflare Tunnel

Engine ko cloud pe nahi daal sakte (webcam chahiye). Laptop pe chalao + tunnel se expose karo.

### 3.1 Engine start karo (jaise abhi kar rahe ho)
Terminal 1 — Backend already Render pe hai, isliye sirf engine:

```bash
# .env mein BACKEND_API_URL update karo:
# BACKEND_API_URL=https://netra-backend.onrender.com/api/ai-stream

cd engine
python netra_engine.py
```

Console mein "Opening camera source -> 0" aana chahiye (webcam).

### 3.2 Cloudflare Tunnel install karo
Cloudflare Tunnel (free) tumhare local port 8001 ko internet pe expose karta hai.

**Windows:**
```powershell
# Download cloudflared.exe
# https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
# Isse cloudflared.exe naam se save karo
```

**Linux/Mac:**
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
```

### 3.3 Tunnel start karo
Naya terminal kholo:

```bash
# Windows
cloudflared.exe tunnel --url http://localhost:8001

# Linux/Mac
./cloudflared tunnel --url http://localhost:8001
```

Console mein ek URL aayega jaise:
```
https://random-words-xxxx.trycloudflare.com
```

YE URL tumhara engine ka public address hai! Jab tak terminal band nahi karte, ye URL kaam karega.

### 3.4 Vercel mein Engine URL update karo
Vercel → Settings → Environment Variables:
- `VITE_ENGINE_URL` = `https://random-words-xxxx.trycloudflare.com`
- Redeploy karo

### 3.5 Backend mein Engine URL update karo (for CORS)
Render → Environment:
- `CORS_ORIGINS` = `https://devdoots-netra.vercel.app`

Backend ke main.py mein CORS origins mein Vercel URL add karna padega:
```python
allow_origins=["http://localhost:5173", "http://localhost:3000",
               "https://devdoots-netra.vercel.app"],
```

Engine mein bhi CORS allow karna padega (FastAPI already `0.0.0.0` pe serve karta hai).

---

## STEP 4: Test karo — sab connected hai?

1. **Frontend** (Vercel): https://devdoots-netra.vercel.app → dashboard khulega
2. **Persons Detected** counter update hona chahiye (engine se backend se frontend)
3. **Live Feed** page: camera + AI feed dono dikhne chahiye
4. **Chatbot**: "hello" type karo → Gemini se proper jawab aana chahiye
5. **SOS test**: haath 3 sec upar rakho → alert + forensic report

### Agar nahi chalta:
- Browser console (F12) kholo — kya errors hain?
- Frontend → Backend: `VITE_BACKEND_URL` sahi hai?
- Frontend → Engine: `VITE_ENGINE_URL` sahi hai? Tunnel alive hai?
- Engine → Backend: `BACKEND_API_URL` Render URL pe set hai?
- CORS errors: backend + engine dono pe deployed domain allow karo

---

## DEMO DAY Checklist

Demo se 15 min pehle ye karo:

1. [ ] Laptop pe engine start karo: `python engine/netra_engine.py`
2. [ ] Cloudflare Tunnel start karo: `cloudflared tunnel --url http://localhost:8001`
3. [ ] Tunnel URL copy karo
4. [ ] Vercel → Settings → `VITE_ENGINE_URL` update karo → Redeploy
5. [ ] Render pe backend running hai check karo
6. [ ] Browser mein frontend kholo — sab kaam kar raha hai?
7. [ ] Webcam pe haath dikhao → person count +2, SOS gesture test

---

## Files Summary

| File | Location | Purpose |
|------|----------|---------|
| `backend/Dockerfile` | `backend/` folder mein | Render pe backend Docker deploy |
| `engine/Dockerfile` | `engine/` folder mein | Local Docker testing (optional) |
| `docker-compose.yml` | Project root | Sab services ek saath local test |
| `frontend/.env.example` | `frontend/` folder mein | Frontend env var template |
| `frontend/vercel.json` | `frontend/` folder mein | Vercel deploy config |
| `render.yaml` | Project root | Render deploy config |


https://devdoots-netra-backend-7hoi.onrender.com/

https://devdoots-netra-jut.vercel.app/