@echo off
echo Starting Project Netra...
start "Backend" cmd /k "cd divyansh_backend && uvicorn main:app --reload"
timeout /t 5

echo Starting Frontend UI...
start cmd /k "cd aryan_task && npm run dev"

echo Starting Engine...
start cmd /k "cd netra_unified_engine.py "
echo System Launched Successfully.
pause