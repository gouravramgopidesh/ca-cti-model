@echo off
cd /d "%~dp0"
docker compose -p ca-cti-model ps
docker compose -p ca-cti-model exec -T chatbot python -m compileall -q /app
powershell -NoProfile -Command "try {$h=Invoke-RestMethod 'http://localhost:3019/api/chat/health'; $h | ConvertTo-Json -Depth 5} catch {Write-Host $_; exit 1}"
pause
