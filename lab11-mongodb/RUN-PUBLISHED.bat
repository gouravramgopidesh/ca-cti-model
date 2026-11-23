@echo off
setlocal
cd /d "%~dp0"
if not exist evidence mkdir evidence
set /p HUB=Enter Docker Hub username: 
if "%HUB%"=="" exit /b 1
set LAB11_IMAGE=%HUB%/lab11-mongodb:1.0
docker pull %LAB11_IMAGE% || exit /b 1
docker compose up -d --wait config shard-a shard-b || exit /b 1
docker compose run --rm --no-deps -T runner python init.py || exit /b 1
docker compose up -d --wait mongos || exit /b 1
docker compose run --rm --no-deps -T runner python init_router.py || exit /b 1
call RUN-LABS.bat
exit /b %errorlevel%
