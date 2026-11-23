@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe configure_atlas.py
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Configuration failed.
pause
exit /b 1
