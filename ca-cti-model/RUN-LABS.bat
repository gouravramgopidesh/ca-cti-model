@echo off
cd /d "%~dp0"
docker compose exec -T app npm run lab71
if errorlevel 1 goto fail
docker compose exec -T app npm run lab72
if errorlevel 1 goto fail
echo Completed. Open the evidence folder for fresh JSON and JSONL results.
pause
exit /b 0
:fail
echo A lab failed. Check the error above.
pause
exit /b 1
