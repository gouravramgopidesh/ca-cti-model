@echo off
setlocal
cd /d "%~dp0"
docker compose run --rm --no-deps -T runner python activity-12.1/rbac.py || goto fail
pause
docker compose run --rm --no-deps -T runner python activity-12.1-try-it-yourself/redaction.py || goto fail
pause
docker compose run --rm --no-deps -T runner python activity-12.2/tls-test.py || goto fail
echo Completed. Evidence is in evidence folder.
pause
exit /b 0
:fail
echo Lab failed. See output above.
pause
exit /b 1
