@echo off
cd /d "%~dp0"
docker compose up -d --wait mongo1 mongo2 mongo3
if errorlevel 1 goto fail
rem Start arbiter process for the later activity; it does not vote until added.
docker compose --profile arbiter up -d --wait arbiter
if errorlevel 1 goto fail
docker compose exec -T mongo1 mongosh --quiet < activity-8.1\replica-set-init.js
if errorlevel 1 goto fail
docker compose --profile tools build runner
if errorlevel 1 goto fail
echo Lab 8 started. Run RUN-LABS.bat next.
pause
exit /b 0
:fail
echo Startup failed. Check Docker Desktop and docker compose logs.
pause
exit /b 1
