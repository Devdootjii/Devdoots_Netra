@echo off
echo Starting Project NETRA (3-process architecture)...
echo.

:: 1. FastAPI Backend  (port 8000)
start "NETRA Backend" cmd /k "cd backend && uvicorn main:app --reload"

timeout /t 3 >nul

:: 2. NETRA Engine  (port 8001 - vision + SOS + Gemini + Drive)
start "NETRA Engine" cmd /k "python engine\netra_engine.py"

timeout /t 2 >nul

:: 3. React Frontend  (port 5173)
start "NETRA Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo All three processes launched:
echo   Backend  : http://127.0.0.1:8000
echo   Engine   : http://127.0.0.1:8001/live-feed
echo   Frontend: http://localhost:5173
echo.
pause
