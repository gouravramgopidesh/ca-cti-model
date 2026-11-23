@echo off
cd /d "%~dp0"
docker pull gouravram77/lab18-mongodb:1.0
if errorlevel 1 goto failed
if not exist evidence mkdir evidence
docker image inspect --format "{{json .RepoDigests}}" gouravram77/lab18-mongodb:1.0 > evidence\published-image.txt
if errorlevel 1 goto failed
docker compose up -d --no-build --wait --wait-timeout 900
if errorlevel 1 goto failed
docker compose up -d --no-build --no-deps --force-recreate app
if errorlevel 1 goto failed
docker compose exec -T -e LAB_RUN_MODE=published app python run_labs.py
if errorlevel 1 goto failed
echo RUN-PUBLISHED succeeded. See evidence\published and reports.
pause
exit /b 0
:failed
echo RUN-PUBLISHED failed. See output above.
pause
exit /b 1
