@echo off
cd /d "%~dp0"
docker compose exec -T -e LAB_RUN_MODE=local app python run_labs.py
if errorlevel 1 goto failed
echo RUN-LABS succeeded. See evidence\local and reports.
pause
exit /b 0
:failed
echo RUN-LABS failed. See output above.
pause
exit /b 1
