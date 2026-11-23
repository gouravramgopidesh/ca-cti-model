@echo off
cd /d "%~dp0"
set /p DHUSER=Enter your Docker Hub username: 
if not defined DHUSER exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File activity-13.2/run-kubernetes.ps1 -Image "%DHUSER%/lab13-mongodb:1.0" || goto fail
pause
exit /b 0
:fail
echo Kubernetes test failed. See output above.
pause
exit /b 1
