@echo off
cd /d "%~dp0"
docker compose --profile arbiter --profile tools down
pause
