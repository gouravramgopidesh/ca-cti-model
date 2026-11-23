@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1 || exit /b 1
set /p HUB=Enter Docker Hub username: 
if "%HUB%"=="" exit /b 1
set LAB12_IMAGE=%HUB%/lab12-mongodb:1.0
docker pull %LAB12_IMAGE% || exit /b 1
docker compose run --rm --no-deps -T certgen || exit /b 1
docker compose up -d --wait mongo mongo-tls || exit /b 1
call RUN-LABS.bat
exit /b %errorlevel%
