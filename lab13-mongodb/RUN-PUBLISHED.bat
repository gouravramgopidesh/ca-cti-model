@echo off
cd /d "%~dp0"
set /p DHUSER=Enter your Docker Hub username: 
if not defined DHUSER exit /b 1
set LAB13_IMAGE=%DHUSER%/lab13-mongodb:1.0
powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1 || goto fail
docker pull %LAB13_IMAGE% || goto fail
docker compose run --rm --no-deps keygen || goto fail
docker compose up -d --wait mongo1 mongo2 mongo3 || goto fail
docker compose run --rm --no-deps runner python activity-13.1/init.py || goto fail
docker compose up -d exporter || goto fail
call RUN-LABS.bat || goto fail
exit /b 0
:fail
echo Published run failed.
pause
exit /b 1
