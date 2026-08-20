@echo off
echo Starting Project Netra - Full Team Sync...

:: 1. Start FastAPI Backend (Divyansh)
start "Backend (Divyansh)" cmd /k "..\.venv\Scripts\activate && cd divyansh_backend && uvicorn main:app --reload"

:: Thoda wait karte hain taaki backend poori tarah on ho jaye
timeout /t 5

:: 2. Start Main AI Hardware Pipeline (Ritesh)
start "AI Pipeline (Ritesh)" cmd /k "..\.venv\Scripts\activate && cd ritesh_task && python ai_hardware_sync.py"

:: 3. Start AI Stability/Processing (Balram)
:: (Note: Screenshot ke hisaab se maine 'balram_task3_freeze.py' daala hai. Agar aaj koi aur file chalani hai toh isko badal lena)
start "AI Process (Balram)" cmd /k "..\.venv\Scripts\activate && cd balram_task && python balram_task3_freeze.py"

:: 4. Start Cloud Alerts & Integrations (Khushi)
:: (Note: Screenshot ke hisaab se maine 'dynamic_camera_alerts.py' daala hai. Agar alert_pipeline chalani ho toh badal lena)
start "Cloud Alerts (Khushi)" cmd /k "..\.venv\Scripts\activate && cd khushi_task && python dynamic_camera_alerts.py"

echo Starting Frontend UI...

:: 5. Start React/Vite Frontend (Aryan)
start "Frontend (Aryan)" cmd /k "cd aryan_task && npm run dev"

echo System Launched Successfully.
pause  