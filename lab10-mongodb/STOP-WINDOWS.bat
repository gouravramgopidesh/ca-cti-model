@echo off
cd /d "%~dp0"
docker compose --profile tools stop
pause
