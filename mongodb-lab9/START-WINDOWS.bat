@echo off
cd /d "%~dp0"
if not exist evidence mkdir evidence
docker compose up -d --wait mongo1 mongo2 mongo3 || goto fail
docker compose build runner || goto fail
docker compose run --rm --no-deps -T runner python init.py || goto fail
echo Lab 9 started. Run RUN-LABS.bat next.
pause
exit /b 0
:fail
echo Startup failed. See output above.
pause
exit /b 1
