@echo off
cd /d "%~dp0"
if not exist evidence mkdir evidence
docker compose run --rm --no-deps  -T runner python activity-10.1/bank-transfer.py || goto fail
pause
docker compose run --rm --no-deps  -T runner python activity-10.1-try-it-yourself/retry-transfer.py || goto fail
pause
docker compose run --rm --no-deps  -T runner python activity-10.2/inventory-reservation.py || goto fail
echo Completed. Evidence is in evidence folder.
pause
exit /b 0
:fail
echo Lab failed. See output above.
pause
exit /b 1

