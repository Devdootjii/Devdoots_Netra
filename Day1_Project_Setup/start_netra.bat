@echo off
echo Starting Project Netra - Full Team Sync...

:: 1. Start FastAPI Backend (Divyansh)
start "Backend (Divyansh)" cmd /k "..\venv\Scripts\activate.bat && cd divyansh_backend && uvicorn main:app --reload"

:: Thoda wait karte hain taaki backend poori tarah on ho jaye
timeout /t 5

:: 2. Start Main AI Hardware Pipeline (Ritesh)
start "AI Pipeline (Ritesh)" cmd /k "..\venv\Scripts\activate.bat && cd ritesh_task && python ai_hardware_sync.py"

:: 3. Start AI Stability/Processing (Balram)
start "AI Process (Balram)" cmd /k "..\venv\Scripts\activate.bat && cd balram_task && python balram_task3_freeze.py"

:: 4. Start Cloud Alerts & Integrations (Khushi)
start "Cloud Alerts (Khushi)" cmd /k "..\venv\Scripts\activate.bat && cd khushi_task && python dynamic_camera_alerts.py"

echo Starting Frontend UI...

:: 5. Start React/Vite Frontend (Aryan)
start "Frontend (Aryan)" cmd /k "cd aryan_task && npm run dev"

echo System Launched Successfully.
pause