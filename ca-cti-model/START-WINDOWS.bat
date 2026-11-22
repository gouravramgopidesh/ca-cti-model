@echo off
cd /d "%~dp0"
docker info >nul 2>&1
if errorlevel 1 (
 echo Open Docker Desktop and wait until its engine is running, then retry.
 pause
 exit /b 1
)
docker compose up --build -d --wait
if errorlevel 1 goto fail
start "" "http://localhost:3000"
echo lab7-mongodb started. Run RUN-LABS.bat to generate fresh lab evidence.
pause
exit /b 0
:fail
echo Startup failed. Check the output and docker compose logs.
pause
exit /b 1
