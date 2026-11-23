@echo off
setlocal
cd /d "%~dp0"
if not exist evidence mkdir evidence
docker compose run --rm --no-deps -T runner python activity-11.1/shard-key-evaluation.py || exit /b 1
pause
type activity-11.1-try-it-yourself\resharding-research.md
pause
docker compose run --rm --no-deps -T runner python activity-11.2/hotspot-detection.py || exit /b 1
echo Completed. Evidence is in evidence folder.
pause
