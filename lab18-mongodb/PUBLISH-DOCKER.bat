@echo off
cd /d "%~dp0"
docker compose build app
if errorlevel 1 goto failed
docker push gouravram77/lab18-mongodb:1.0
if errorlevel 1 goto failed
echo PUBLISH-DOCKER succeeded.
pause
exit /b 0
:failed
echo PUBLISH-DOCKER failed. See output above.
pause
exit /b 1
