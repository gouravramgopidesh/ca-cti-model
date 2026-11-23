@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe make_submission.py
pause
