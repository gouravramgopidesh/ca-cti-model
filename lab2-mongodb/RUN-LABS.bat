@echo off
cd /d "%~dp0"
if not exist .env (
 copy .env.example .env >nul
 echo Edit .env with your Atlas URI, then run again.
 notepad .env
 exit /b 1
)
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
for %%F in (activity-2.1\setup_environment.py activity-2.1-try\compare_servers.py activity-2.2\books_crud.py activity-2.2-try\update_prices.py) do (
 echo ==== %%F ====
 .venv\Scripts\python.exe "%%F"
 if errorlevel 1 goto fail
)
echo LAB 2 PASSED: all four activities.
pause
exit /b 0
:fail
echo Lab failed. Check Atlas URI, IP access and local MongoDB service. Do not share credentials.
pause
exit /b 1
