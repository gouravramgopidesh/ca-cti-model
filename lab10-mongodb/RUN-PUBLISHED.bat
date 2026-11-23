@echo off
cd /d "%~dp0"
set /p HUB=Enter Docker Hub username: 
if "%HUB%"=="" exit /b 1
set LAB10_IMAGE=%HUB%/lab10-mongodb:1.0
docker pull %LAB10_IMAGE% || exit /b 1
if not exist evidence mkdir evidence
docker compose up -d --wait mongo1 mongo2 mongo3 || exit /b 1
docker compose run --rm --no-deps  -T runner python init.py || exit /b 1
call RUN-LABS.bat
exit /b %errorlevel%

