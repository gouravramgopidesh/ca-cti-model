@echo off
cd /d "%~dp0"
set /p HUB_USER=Enter Docker Hub username: 
if not defined HUB_USER exit /b 1
set "LAB_IMAGE=%HUB_USER%/lab15-mongodb:1.0"
docker pull %LAB_IMAGE%
if errorlevel 1 goto failed
docker compose up -d --no-build --force-recreate --wait app
if errorlevel 1 goto failed
docker compose exec -T app python run_labs.py
if errorlevel 1 goto failed
echo Published Lab 15 passed.
pause
exit /b 0
:failed
echo Published Lab 15 failed. See output above.
pause
exit /b 1
