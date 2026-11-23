@echo off
cd /d "%~dp0"
docker compose run --rm --no-deps -T runner python activity-9.1/benchmark.py || goto fail
pause
docker compose run --rm --no-deps -T runner python activity-9.1-try-it-yourself/journaling.py || goto fail
pause
powershell -NoProfile -ExecutionPolicy Bypass -File activity-9.2\run-partition.ps1 || goto fail
echo Completed. Evidence is in evidence folder.
pause
exit /b 0
:fail
echo Experiment failed. See output above.
pause
exit /b 1
