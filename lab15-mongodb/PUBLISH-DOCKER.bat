@echo off
cd /d "%~dp0"

docker compose build app
if errorlevel 1 goto failed

docker push gouravram77/lab15-mongodb:1.0
if errorlevel 1 goto failed

echo.
echo Published gouravram77/lab15-mongodb:1.0
echo https://hub.docker.com/r/gouravram77/lab15-mongodb
pause
exit /b 0

:failed
echo Publishing failed.
pause
exit /b 1