@echo off
echo Starting Project Netra...
start "Backend" cmd /k "cd Day1_Project_Setup\divyansh_backend && python -m uvicorn main:app --reload"
timeout /t 5
start "AI Pipeline" cmd /k "cd Day1_Project_Setup\balram_task && python balram_task3_freeze.py"
start "Ritesh Task" cmd /k "cd Day1_Project_Setup\ritesh_task && python ai_hardware_sync.py"
start "Frontend" cmd /k "cd Day1_Project_Setup\aryan_task && npm run dev"
echo System Launched Successfully.
pause