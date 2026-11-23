@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
for %%F in (activity-3.1\embedded_courses.py activity-3.1-try\prerequisites.py activity-3.2\migrate_blog.py activity-3.2-try\large_comments.py) do (
  echo ==== %%F ====
  .venv\Scripts\python.exe "%%F"
  if errorlevel 1 goto fail
  echo Capture the actual output screenshot before continuing.
  pause
)
echo LAB 3 PASSED: all four activities.
pause
exit /b 0
:fail
echo LAB FAILED. Check the error and local MongoDB service.
pause
exit /b 1
