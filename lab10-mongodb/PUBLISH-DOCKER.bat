@echo off
cd /d "%~dp0"
set /p HUB=Enter your Docker Hub username: 
if "%HUB%"=="" exit /b 1
docker login || exit /b 1
docker compose build runner || exit /b 1
docker tag lab10-mongodb-runner:local %HUB%/lab10-mongodb:1.0 || exit /b 1
docker push %HUB%/lab10-mongodb:1.0 || exit /b 1
echo Repository: https://hub.docker.com/r/%HUB%/lab10-mongodb
pause
