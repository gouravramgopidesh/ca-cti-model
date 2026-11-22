@echo off
cd /d "%~dp0"
echo Starting standalone ca-cti-model Docker group...
docker compose -p ca-cti-model up -d --build || goto :fail
echo Loading local Ollama models...
docker compose -p ca-cti-model exec -T ollama ollama pull qwen2.5:3b || goto :fail
docker compose -p ca-cti-model exec -T ollama ollama pull all-minilm || goto :fail
echo Ingesting knowledge into this project database...
docker compose -p ca-cti-model exec -T chatbot python ingest.py || goto :fail
echo.
echo Open http://localhost:3019/#assistant
docker compose -p ca-cti-model ps
pause
exit /b 0
:fail
echo.
echo Startup was interrupted or failed. Check the error above.
docker compose -p ca-cti-model ps
pause
exit /b 1
