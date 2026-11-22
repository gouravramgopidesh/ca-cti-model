@echo off
cd /d "%~dp0"
echo === Checking standalone CA Docker stack ===
docker compose -p ca-cti-model up -d --build || goto :fail
echo === Checking local models ===
docker compose -p ca-cti-model exec -T ollama ollama pull qwen2.5:3b || goto :fail
docker compose -p ca-cti-model exec -T ollama ollama pull all-minilm || goto :fail
echo === Indexing Lab source documents and local CTI collections ===
docker compose -p ca-cti-model exec -T chatbot python ingest.py || goto :fail
echo === Service readiness and source counts ===
docker compose -p ca-cti-model exec -T chatbot python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8000/health',timeout=8).read().decode())" || goto :fail
echo === Test chatbot classification and basic math ===
docker compose -p ca-cti-model exec -T chatbot python test_logic.py || goto :fail
echo === Docker services ===
docker compose -p ca-cti-model ps
echo.
echo Open http://localhost:3019/#assistant and start New conversation.
pause
exit /b 0
:fail
echo FAILED. The error above identifies the step. Existing volumes have not been deleted.
docker compose -p ca-cti-model ps
pause
exit /b 1
