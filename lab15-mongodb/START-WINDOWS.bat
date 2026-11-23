@echo off
cd /d "%~dp0"
docker compose up -d --build --wait
if errorlevel 1 goto failed
echo Lab 15 started. Swagger UI: http://localhost:3015/docs
pause
exit /b 0
:failed
echo Lab 15 startup failed.
pause
exit /b 1
