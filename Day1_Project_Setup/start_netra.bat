@echo off
echo Starting Project Netra...
start "Backend" cmd /k "cd divyansh_backend && uvicorn main:app --reload"
timeout /t 5
start "AI Pipeline" cmd /k "cd balram_yolo_test && python master_ai_script.py"
echo Starting Frontend UI...
start cmd /k "cd aryan_task && npm run dev"
echo System Launched Successfully.
pause