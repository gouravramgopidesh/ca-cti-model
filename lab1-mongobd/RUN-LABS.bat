@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
python "activity-1.1\classify_databases.py"
if errorlevel 1 goto failed
echo Capture the actual output before continuing.
pause
echo.
python "activity-1.1-try\research_database.py"
if errorlevel 1 goto failed
echo Capture the actual output before continuing.
pause
echo.
python "activity-1.2\map_application.py"
if errorlevel 1 goto failed
echo Capture the actual output before continuing.
pause
echo.
python "activity-1.2-try\map_cti.py"
if errorlevel 1 goto failed
echo Capture the actual output before continuing.
pause
echo LAB 1 PASSED: all four activities.
pause
exit /b 0
:failed
echo Lab 1 failed. Check the error above and verify MongoDB is running.
pause
exit /b 1
