@echo off
cd /d "%~dp0"
docker compose --profile metrics stop
pause
