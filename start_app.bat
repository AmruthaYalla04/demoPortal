@echo off
echo =====================================================
echo     GitHub Repository Runner - Startup
echo =====================================================
echo Starting the unified application...
echo.
echo PORTS:
echo   - Main application: Frontend 3002, Backend 8002
echo   - Cloned repository (when run): Frontend 3000, Backend 8000
echo.
echo Wait while the application starts...
echo.

REM Check for port conflicts
echo Checking for processes using required ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3002') do (
    echo Port 3002 in use, attempting to free...
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002') do (
    echo Port 8002 in use, attempting to free...
    taskkill /F /PID %%a >nul 2>&1
)

REM Set environment variable to force React to use port 3002
set PORT=3002

REM Start the main application using the merged backend
cd /d "%~dp0\backend"
python main.py

echo.
echo If the application did not start correctly, make sure you have
echo Python and all required dependencies installed.
echo.
pause
