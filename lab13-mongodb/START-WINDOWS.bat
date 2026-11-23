@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1 || goto fail
docker compose build runner || goto fail
docker compose run --rm --no-deps keygen || goto fail
docker compose up -d --wait mongo1 mongo2 mongo3 || goto fail
docker compose run --rm --no-deps runner python activity-13.1/init.py || goto fail
docker compose up -d exporter || goto fail
echo Lab 13 Compose started. Run RUN-LABS.bat next.
pause
exit /b 0
:fail
echo Startup failed. See output above.
pause
exit /b 1
