@echo off
setlocal
cd /d "%~dp0"
if not exist evidence mkdir evidence
docker compose stop
pause
