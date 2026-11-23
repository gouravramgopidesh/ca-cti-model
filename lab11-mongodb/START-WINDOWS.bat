@echo off
setlocal
cd /d "%~dp0"
if not exist evidence mkdir evidence
docker compose up -d --wait config shard-a shard-b || exit /b 1
docker compose build runner || exit /b 1
docker compose run --rm --no-deps -T runner python init.py || exit /b 1
docker compose up -d --wait mongos || exit /b 1
docker compose run --rm --no-deps -T runner python init_router.py || exit /b 1
echo Lab 11 started. Run RUN-LABS.bat next.
pause
