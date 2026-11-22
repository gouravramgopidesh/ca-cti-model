@echo off
cd /d "%~dp0"
docker compose ps
docker compose exec chatbot python test_logic.py
echo Browser: http://localhost:3019/#assistant
pause
