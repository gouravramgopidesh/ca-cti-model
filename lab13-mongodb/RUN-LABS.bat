@echo off
cd /d "%~dp0"
docker compose run --rm --no-deps runner python activity-13.1/failover.py || goto fail
pause
docker compose run --rm --no-deps runner python activity-13.1-try-it-yourself/metrics.py || goto fail
echo Compose activities passed. Publish image and run Kubernetes separately.
pause
exit /b 0
:fail
echo Lab failed. See output above.
pause
exit /b 1
