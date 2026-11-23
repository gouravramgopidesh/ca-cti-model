@echo off
cd /d "%~dp0"
set /p HUB=Enter your Docker Hub username: 
if "%HUB%"=="" exit /b 1
docker login || exit /b 1
docker compose build runner || exit /b 1
docker tag mongodb-lab9-runner:local %HUB%/mongodb-lab9:1.0 || exit /b 1
docker push %HUB%/mongodb-lab9:1.0 || exit /b 1
echo Repository: https://hub.docker.com/r/%HUB%/mongodb-lab9
pause
