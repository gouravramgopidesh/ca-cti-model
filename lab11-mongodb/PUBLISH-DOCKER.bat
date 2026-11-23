@echo off
setlocal
cd /d "%~dp0"
if not exist evidence mkdir evidence
set /p HUB=Enter Docker Hub username: 
if "%HUB%"=="" exit /b 1
set LAB11_IMAGE=
docker login || exit /b 1
docker compose build runner || exit /b 1
docker tag lab11-mongodb-runner:local %HUB%/lab11-mongodb:1.0 || exit /b 1
docker push %HUB%/lab11-mongodb:1.0 || exit /b 1
echo Repository: https://hub.docker.com/r/%HUB%/lab11-mongodb
pause
