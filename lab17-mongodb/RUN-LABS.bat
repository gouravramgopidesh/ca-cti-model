@echo off
cd /d "%~dp0"
docker compose exec -T app python run_labs.py
if errorlevel 1 goto failed
echo RUN-LABS succeeded.
pause
exit /b 0
:failed
echo RUN-LABS failed. See output above.
pause
exit /b 1
