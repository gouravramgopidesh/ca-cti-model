@echo off
cd /d "%~dp0"
docker compose up -d --build --wait --wait-timeout 900
if errorlevel 1 goto failed
echo START-WINDOWS succeeded.
pause
exit /b 0
:failed
echo START-WINDOWS failed. See output above.
pause
exit /b 1
