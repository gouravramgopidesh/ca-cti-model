@echo off
cd /d "%~dp0"
docker compose exec -T app python run_labs.py
if errorlevel 1 goto failed
echo Lab 15 passed. See evidence folder.
pause
exit /b 0
:failed
echo Lab 15 failed. See output above.
pause
exit /b 1
