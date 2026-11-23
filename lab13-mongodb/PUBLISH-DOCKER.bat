@echo off
cd /d "%~dp0"
set /p DHUSER=Enter your Docker Hub username: 
if not defined DHUSER exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1 || goto fail
docker login || goto fail
docker compose build runner || goto fail
docker tag lab13-mongodb-runner:local %DHUSER%/lab13-mongodb:1.0 || goto fail
docker push %DHUSER%/lab13-mongodb:1.0 || goto fail
echo Repository: https://hub.docker.com/r/%DHUSER%/lab13-mongodb
pause
exit /b 0
:fail
echo Publish failed.
pause
exit /b 1
