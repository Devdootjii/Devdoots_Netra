@echo off
echo Starting Project Netra...

:: 1. Start FastApi Backend (Auto-activates .venv)
start "Backend" cmd /k "..\.venv\Scripts\activate && cd divyansh_backend && uvicorn main:app --reload"

timeout /t 5

:: 2. Start Ritesh's AI Pipeline (Auto-activates .venv)
start "AI Pipeline" cmd /k "..\.venv\Scripts\activate && cd ritesh_task && python ai_hardware_sync.py"

echo Starting Frontend UI...

:: 3. Start React/Next.js Frontend
start "Frontend" cmd /k "cd aryan_task && npm run dev"

echo System Launched Successfully.
pause