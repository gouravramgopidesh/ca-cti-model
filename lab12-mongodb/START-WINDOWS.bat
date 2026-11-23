@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1 || exit /b 1
docker compose build runner || exit /b 1
docker compose run --rm --no-deps -T certgen || exit /b 1
docker compose up -d --wait mongo mongo-tls || exit /b 1
echo Lab 12 started. Run RUN-LABS.bat next.
pause
