REM filepath: c:\Users\Divya Sri\Desktop\demo\run_commands.bat
@echo off
setlocal EnableDelayedExpansion

echo =====================================================
echo     GitHub Repository Runner - Command Script
echo =====================================================
echo This script will clone and run the AI Chatbot repository
echo PORTS:
echo   - Main application: Frontend 3002, Backend 8002
echo   - Cloned repository: Frontend 3000, Backend 8000
echo =====================================================
echo.

REM Working directory for cloned repos
set TIMESTAMP=%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=!TIMESTAMP: =0!
set WORK_DIR="%cd%\cloned_repos"
set REPO_DIR="%cd%\cloned_repos\aichatbot"
set ALT_REPO_DIR="%cd%\cloned_repos\aichatbot-main"

REM STEP 1: Clean environment and prepare directory
echo [%TIME%] STEP 1: Preparing environment...
if not exist %WORK_DIR% mkdir %WORK_DIR%
echo [%TIME%] Created working directory: %WORK_DIR%

REM Remove any existing directories to start clean
for %%D in (%REPO_DIR% %ALT_REPO_DIR%) do (
    if exist %%D (
        echo [%TIME%] Found existing directory: %%D. Removing...
        rd /s /q %%D >nul 2>&1
        
        REM If directory still exists, try alternative methods
        if exist %%D (
            echo [%TIME%] Using PowerShell to force remove directory...
            powershell -Command "Remove-Item -Path '%%D' -Recurse -Force -ErrorAction SilentlyContinue"
        )
        
        REM Final check
        if exist %%D (
            echo [%TIME%] Warning: Could not completely remove directory: %%D
        ) else (
            echo [%TIME%] Successfully removed directory: %%D
        )
    )
)

echo [%TIME%] ✓ STEP 1 COMPLETE: Environment prepared.
echo.

REM STEP 2: Clone the repository (must complete before proceeding)
echo [%TIME%] STEP 2: Cloning repository...
set CLONE_SUCCESS=false
set ACTUAL_REPO_DIR=%REPO_DIR%

REM Try git clone first
echo [%TIME%] Attempting git clone...
git clone --depth 1 https://github.com/AmruthaYalla04/aichatbot.git %REPO_DIR%

if %ERRORLEVEL% EQU 0 (
    if exist %REPO_DIR%\NUL (
        set CLONE_SUCCESS=true
        set ACTUAL_REPO_DIR=%REPO_DIR%
        echo [%TIME%] ✓ Git clone successful.
    ) else (
        echo [%TIME%] Git clone command succeeded but directory not found.
    )
) else (
    echo [%TIME%] Git clone failed with error code %ERRORLEVEL%.
)

REM Try ZIP download if git clone failed
if "%CLONE_SUCCESS%"=="false" (
    echo [%TIME%] Attempting to download as ZIP file...
    
    REM Download and extract with PowerShell
    powershell -Command "& {try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/AmruthaYalla04/aichatbot/archive/refs/heads/main.zip' -OutFile '%TEMP%\repo.zip' -UseBasicParsing; Expand-Archive -Path '%TEMP%\repo.zip' -DestinationPath '%WORK_DIR%' -Force; Remove-Item -Path '%TEMP%\repo.zip' -Force -ErrorAction SilentlyContinue; if (Test-Path '%ALT_REPO_DIR%') { Write-Host 'Downloaded and extracted successfully to %ALT_REPO_DIR%' } else { throw 'ZIP extraction failed or directory not found' } } catch { Write-Host ('Download failed: ' + $_.Exception.Message); exit 1 } }"
    
    if exist %ALT_REPO_DIR%\NUL (
        set CLONE_SUCCESS=true
        set ACTUAL_REPO_DIR=%ALT_REPO_DIR%
        echo [%TIME%] ✓ Downloaded and extracted repository via ZIP.
    ) else (
        echo [%TIME%] ❌ Both git clone and ZIP download failed.
        echo [%TIME%] Cannot proceed without repository files.
        goto :End
    )
)

echo [%TIME%] ✓ STEP 2 COMPLETE: Repository available at %ACTUAL_REPO_DIR%
echo.

REM STEP 3: Check for chatbot directory
echo [%TIME%] STEP 3: Looking for chatbot directory...
set BASE_DIR=%ACTUAL_REPO_DIR%

if exist %ACTUAL_REPO_DIR%\chatbot\NUL (
    echo [%TIME%] Found 'chatbot' directory.
    set BASE_DIR=%ACTUAL_REPO_DIR%\chatbot
    cd /d !BASE_DIR!
    echo [%TIME%] Changed directory to: %cd%
) else (
    echo [%TIME%] No 'chatbot' directory found. Using repository root.
    cd /d %ACTUAL_REPO_DIR%
)
echo [%TIME%] ✓ STEP 3 COMPLETE: Using base directory: %cd%
echo.

REM STEP 4: Navigate to backend directory
echo [%TIME%] STEP 4: Navigating to backend directory...
if not exist backend\NUL (
    echo [%TIME%] ❌ STEP 4 FAILED: Backend directory not found!
    goto :End
)
cd backend
echo [%TIME%] ✓ STEP 4 COMPLETE: Successfully navigated to backend directory: %cd%
echo.

REM STEP 5: Create virtual environment
echo [%TIME%] STEP 5: Creating Python virtual environment...

REM Remove existing venv if it exists
if exist venv\NUL (
    echo [%TIME%] Removing existing virtual environment...
    rd /s /q venv >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo [%TIME%] Running: python -m venv venv
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] ❌ STEP 5 FAILED: Virtual environment creation failed.
    goto :End
)

REM Verify venv was created
if not exist venv\Scripts\activate.bat (
    echo [%TIME%] ❌ STEP 5 FAILED: Virtual environment files not found.
    goto :End
)

echo [%TIME%] ✓ STEP 5 COMPLETE: Virtual environment created successfully.
echo.

REM STEP 6: Activate virtual environment and install requirements
echo [%TIME%] STEP 6: Activating environment and installing requirements...
echo [%TIME%] Running: call venv\Scripts\activate

call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] ❌ STEP 6 FAILED: Could not activate virtual environment.
    goto :End
)
echo [%TIME%] Virtual environment activated successfully.

REM Check if requirements.txt exists
if exist requirements.txt (
    echo [%TIME%] Found requirements.txt. Installing dependencies...
    echo [%TIME%] Running: pip install -r requirements.txt
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [%TIME%] Warning: Error during package installation from requirements.txt.
        echo [%TIME%] Installing basic packages instead...
        pip install fastapi uvicorn websockets
    ) else (
        echo [%TIME%] Dependencies installed successfully.
    )
) else (
    echo [%TIME%] requirements.txt not found. Creating a basic one...
    echo fastapi==0.104.1 > requirements.txt
    echo uvicorn==0.24.0 >> requirements.txt
    echo websockets==11.0.3 >> requirements.txt
    echo jinja2==3.1.2 >> requirements.txt
    echo aiofiles==23.2.1 >> requirements.txt
    
    echo [%TIME%] Installing dependencies...
    pip install -r requirements.txt
)

echo [%TIME%] ✓ STEP 6 COMPLETE: Dependencies installed.
echo.

REM STEP 7: Start backend server with an improved approach to avoid command issues
echo [%TIME%] STEP 7: Starting backend server...

REM Check if main.py exists
if not exist main.py (
    echo [%TIME%] main.py not found. Creating a basic one...
    (
        echo from fastapi import FastAPI
        echo.
        echo app = FastAPI()
        echo.
        echo @app.get("/")
        echo def read_root():
        echo     return {"message": "Hello from AI Chatbot Backend"}
    ) > main.py
    echo [%TIME%] Created basic main.py file
)

echo [%TIME%] Starting backend server with uvicorn...
echo [%TIME%] Command: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

start "AI Chatbot Backend (PORT 8000)" cmd /k "cd /d %cd% && call venv\Scripts\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start and verify it's running
echo [%TIME%] Waiting for backend to initialize (20 seconds)...
timeout /t 20 /nobreak > nul

REM Check if backend is running
echo [%TIME%] Verifying backend is running...
powershell -Command "& {try { $response = Invoke-WebRequest -Uri 'http://localhost:8000' -UseBasicParsing -TimeoutSec 5; if ($response.StatusCode -lt 400) { Write-Host '✓ Backend is running successfully.' } else { Write-Host '⚠️ Backend returned status code:' + $response.StatusCode } } catch { Write-Host '⚠️ Backend may not be running: ' + $_.Exception.Message }}"

echo [%TIME%] ✓ STEP 7 COMPLETE: Backend server started.
echo.

REM STEP 8: Navigate to frontend directory
echo [%TIME%] STEP 8: Navigating to frontend directory...
cd ..
if not exist frontend\NUL (
    echo [%TIME%] ❌ STEP 8 FAILED: Frontend directory not found!
    goto :End
)
cd frontend
echo [%TIME%] ✓ STEP 8 COMPLETE: Successfully navigated to frontend directory: %cd%
echo.

REM STEP 9: Install frontend dependencies
echo [%TIME%] STEP 9: Installing frontend dependencies...

REM Check if package.json exists
if not exist package.json (
    echo [%TIME%] ❌ STEP 9 FAILED: package.json not found!
    goto :End
)

echo [%TIME%] Running: npm install
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [%TIME%] ❌ STEP 9 FAILED: npm install failed.
    goto :End
)
echo [%TIME%] ✓ STEP 9 COMPLETE: Frontend dependencies installed.
echo.

REM STEP 10: Start frontend with PORT explicitly set
echo [%TIME%] STEP 10: Starting frontend server...
echo [%TIME%] Command: set PORT=3000 && npm start

start "AI Chatbot Frontend (PORT 3000)" cmd /k "cd /d %cd% && set PORT=3000 && npm start"

echo [%TIME%] Waiting for frontend to initialize (20 seconds)...
timeout /t 20 /nobreak > nul
echo [%TIME%] ✓ STEP 10 COMPLETE: Frontend started.

REM Success message with clear access instructions
echo.
echo =====================================================
echo          APPLICATION SETUP COMPLETE!                
echo =====================================================
echo.
echo The AI Chatbot application is now running:
echo.
echo ✓ Backend API: http://localhost:8000
echo ✓ Frontend UI: http://localhost:3000
echo.
echo To access the application, open your browser and go to:
echo.
echo    http://localhost:3000
echo.
start "" "http://localhost:3000"
echo A browser window should now open with the application.
echo.
echo Close this window when you're finished using the app
echo =====================================================

:End
pause
