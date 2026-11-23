@echo off
setlocal
cd /d "%~dp0"
set /p HUB=Enter Docker Hub username: 
if "%HUB%"=="" exit /b 1
set LAB12_IMAGE=lab12-mongodb-runner:local
docker login || exit /b 1
docker compose build runner || exit /b 1
docker tag %LAB12_IMAGE% %HUB%/lab12-mongodb:1.0 || exit /b 1
docker push %HUB%/lab12-mongodb:1.0 || exit /b 1
echo Repository: https://hub.docker.com/r/%HUB%/lab12-mongodb
pause
