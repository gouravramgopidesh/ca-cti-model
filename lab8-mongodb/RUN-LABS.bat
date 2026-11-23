@echo off
cd /d "%~dp0"
docker compose --profile tools build runner
if errorlevel 1 goto fail
for %%F in (activity-8.1/replica-set-init.py activity-8.1-try-it-yourself/add-arbiter.py activity-8.2/failover-monitor.py activity-8.2-try-it-yourself/priority-election.py) do (
  docker compose run --rm --no-deps runner %%F
  if errorlevel 1 goto fail
  echo Capture a real screenshot of the output above before continuing.
  pause
)
echo Completed. Evidence is in the evidence folder.
pause
exit /b 0
:fail
echo Lab failed. Inspect output and docker compose logs.
pause
exit /b 1
