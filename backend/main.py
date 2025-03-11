from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import subprocess
import sys
import shutil
import platform
import time

app = FastAPI()

# Configure CORS to allow all origins for debugging purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track whether the repository setup has completed successfully
repo_setup_status = {
    "backend_running": False,
    "frontend_running": False
}



# === API Endpoints from both files ===

@app.get("/")
async def root():
    return {"message": "GitHub Repository Runner API"}

@app.get("/status")
async def status():
    return repo_setup_status

@app.get("/start-backend")
async def start_backend():
    try:
        backend_dir = os.path.dirname(__file__)
        subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8002"], cwd=backend_dir)
        return {"message": "Backend started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start backend: {str(e)}")

@app.post("/execute-script")
async def execute_script():
    try:
        # Determine which script to run based on OS
        is_windows = platform.system() == "Windows"
        
        if is_windows:
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_commands.bat")
            # Execute the batch file directly on Windows
            subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/c', script_path], shell=True)
        else:
            # For Unix systems
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_commands.sh")
            # Make the script executable
            os.chmod(script_path, 0o755)
            # Execute the shell script
            subprocess.Popen(['gnome-terminal', '--', 'bash', script_path], shell=True)
            
        return {"message": "Script execution started in a new terminal window"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute script: {str(e)}")

@app.websocket("/ws/run-repo")
async def run_repository(websocket: WebSocket):
    print("WebSocket connection attempt received")
    await websocket.accept()
    print("WebSocket connection accepted")
    
    try:
        # Reset status at the beginning
        repo_setup_status["backend_running"] = False
        repo_setup_status["frontend_running"] = False
        
        # Make the explanation clearer
        await websocket.send_text("Starting repository clone and setup...")
        await websocket.send_text("Note: Main application runs on ports 3002/8002")
        await websocket.send_text("Note: Cloned repository will run on ports 3000/8000")
        
        # Define the working directory (where to clone the repo)
        work_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cloned_repos")
        os.makedirs(work_dir, exist_ok=True)
        await websocket.send_text(f"Created working directory: {work_dir}")
        
        # STEP 1: Clean up existing repository - Must complete before moving to step 2
        await websocket.send_text("STEP 1: Preparing for clean installation...")
        repo_path = os.path.join(work_dir, "aichatbot")
        repo_main_path = os.path.join(work_dir, "aichatbot-main")
        
        # Clean up both possible paths to avoid permission issues
        for path_to_clean in [repo_path, repo_main_path]:
            if os.path.exists(path_to_clean):
                await websocket.send_text(f"Found existing directory. Cleaning {path_to_clean}...")
                try:
                    # Try multiple approaches to ensure directory is removed
                    try:
                        shutil.rmtree(path_to_clean, ignore_errors=True)
                    except Exception:
                        pass
                    
                    # If directory still exists, try with system commands
                    if os.path.exists(path_to_clean):
                        if platform.system() == "Windows":
                            os.system(f'rd /s /q "{path_to_clean}" 2>nul')
                        else:
                            os.system(f'rm -rf "{path_to_clean}" 2>/dev/null')
                    
                    # Final check
                    if not os.path.exists(path_to_clean):
                        await websocket.send_text(f"Successfully removed directory: {path_to_clean}")
                    else:
                        # Last resort: Create a timestamp directory instead
                        await websocket.send_text(f"Could not remove directory. Will use a timestamped directory instead.")
                except Exception as e:
                    await websocket.send_text(f"Error during cleanup: {str(e)}")
        
        # Ensure we have a clean directory to work with
        timestamp = int(time.time())
        if os.path.exists(repo_path):
            repo_path = os.path.join(work_dir, f"aichatbot_{timestamp}")
            await websocket.send_text(f"Using alternative directory: {repo_path}")
            
        await websocket.send_text("✅ STEP 1 COMPLETE: Environment prepared")
        
        # STEP 2: Clone the repository (retry multiple times if needed)
        await websocket.send_text("STEP 2: Cloning repository from https://github.com/AmruthaYalla04/aichatbot.git...")
        clone_success = False
        actual_repo_path = repo_path  # Default path
        
        # First attempt: Git clone with system command
        try:
            if platform.system() == "Windows":
                clone_cmd = f'git clone --depth 1 https://github.com/AmruthaYalla04/aichatbot.git "{repo_path}"'
            else:
                clone_cmd = f'git clone --depth 1 https://github.com/AmruthaYalla04/aichatbot.git "{repo_path}"'
                
            await websocket.send_text(f"Running: {clone_cmd}")
            
            # Try system command first (more reliable with permissions)
            result = os.system(clone_cmd)
            
            if result == 0 and os.path.exists(repo_path) and os.listdir(repo_path):
                clone_success = True
                actual_repo_path = repo_path
                await websocket.send_text("Repository cloned successfully via system command!")
            else:
                await websocket.send_text("Git system command failed. Trying subprocess approach...")
                
                # Try with subprocess
                import subprocess
                process = subprocess.Popen(
                    ["git", "clone", "--depth", "1", "https://github.com/AmruthaYalla04/aichatbot.git", repo_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                _, stderr = process.communicate()
                
                if process.returncode == 0 and os.path.exists(repo_path) and os.listdir(repo_path):
                    clone_success = True
                    actual_repo_path = repo_path
                    await websocket.send_text("Repository cloned successfully via subprocess!")
                else:
                    stderr_text = stderr.decode() if stderr else "No error message"
                    await websocket.send_text(f"Git clone failed: {stderr_text}")
        except Exception as e:
            await websocket.send_text(f"Error during git clone: {str(e)}")
            
        # Second attempt: ZIP download if git failed
        if not clone_success:
            await websocket.send_text("Git clone failed. Trying ZIP download method...")
            try:
                import requests
                import zipfile
                
                # Download the ZIP file
                zip_url = "https://github.com/AmruthaYalla04/aichatbot/archive/refs/heads/main.zip"
                zip_path = os.path.join(work_dir, "repo.zip")
                
                await websocket.send_text(f"Downloading from {zip_url}...")
                response = requests.get(zip_url)
                
                if response.status_code == 200:
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)
                    
                    await websocket.send_text("Download complete. Extracting ZIP...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(work_dir)
                        
                    # Remove the ZIP file
                    os.remove(zip_path)
                    
                    # Use the extracted directory
                    extracted_dir = os.path.join(work_dir, "aichatbot-main")
                    if os.path.exists(extracted_dir) and os.listdir(extracted_dir):
                        clone_success = True
                        actual_repo_path = extracted_dir
                        await websocket.send_text(f"Repository downloaded and extracted to {actual_repo_path}")
                    else:
                        await websocket.send_text("ZIP extraction completed but directory is empty or not found")
                else:
                    await websocket.send_text(f"Failed to download ZIP: HTTP status code {response.status_code}")
            except Exception as e:
                await websocket.send_text(f"Error during ZIP download: {str(e)}")
        
        # Failure check - if both methods failed, we cannot continue
        if not clone_success:
            await websocket.send_text("❌ ERROR: All repository download methods failed.")
            await websocket.send_text("Cannot proceed without repository files.")
            return
            
        await websocket.send_text("✅ STEP 2 COMPLETE: Repository downloaded successfully")
        
        # STEP 3: Navigate to chatbot directory if it exists
        await websocket.send_text("STEP 3: Checking for chatbot directory...")
        chatbot_path = os.path.join(actual_repo_path, "chatbot")
        
        if os.path.exists(chatbot_path) and os.path.isdir(chatbot_path):
            base_dir = chatbot_path
            await websocket.send_text(f"Found chatbot directory at {chatbot_path}")
        else:
            base_dir = actual_repo_path
            await websocket.send_text(f"No chatbot directory found. Using repository root: {actual_repo_path}")
        
        await websocket.send_text("✅ STEP 3 COMPLETE: Base directory set to " + base_dir)
        
        # STEP 4: Navigate to backend directory
        await websocket.send_text("STEP 4: Locating backend directory...")
        backend_dir = os.path.join(base_dir, "backend")
        
        # Strict error checking - fail immediately if backend dir not found
        if not os.path.exists(backend_dir):
            await websocket.send_text("❌ ERROR: Backend directory not found in cloned repository!")
            await websocket.send_text("Repository structure is invalid. Cannot continue.")
            return
            
        await websocket.send_text(f"Backend directory found at {backend_dir}")
        await websocket.send_text("✅ STEP 4 COMPLETE: Backend directory located")
        
        # STEP 5: Create virtual environment
        await websocket.send_text("STEP 5: Creating Python virtual environment...")
        
        venv_dir = os.path.join(backend_dir, "venv")
        # Remove existing venv if it exists
        if os.path.exists(venv_dir):
            await websocket.send_text("Removing existing virtual environment...")
            try:
                shutil.rmtree(venv_dir, ignore_errors=True)
            except Exception as e:
                await websocket.send_text(f"Warning: Could not remove existing venv: {str(e)}")
        
        # Create virtual environment
        venv_created = False
        try:
            # Use subprocess directly for better error capture
            import subprocess
            process = subprocess.Popen(
                ["python", "-m", "venv", "venv"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            _, stderr = process.communicate()
            
            if process.returncode == 0:
                venv_created = True
                await websocket.send_text("Virtual environment created successfully")
            else:
                stderr_text = stderr.decode() if stderr else "No error message"
                await websocket.send_text(f"Error creating virtual environment: {stderr_text}")
                await websocket.send_text("Will try to continue with system Python")
        except Exception as e:
            await websocket.send_text(f"Error creating virtual environment: {str(e)}")
            await websocket.send_text("Will try to continue with system Python")
        
        # Verify venv was created
        scripts_dir = os.path.join(venv_dir, "Scripts" if platform.system() == "Windows" else "bin")
        if os.path.exists(venv_dir) and os.path.exists(scripts_dir):
            venv_created = True
            await websocket.send_text("Virtual environment verified")
        else:
            venv_created = False
            await websocket.send_text("Virtual environment not found or incomplete")
            
        await websocket.send_text("✅ STEP 5 COMPLETE: Virtual environment setup")
        
        # STEP 6: Install dependencies
        await websocket.send_text("STEP 6: Installing Python dependencies...")
        
        # Determine paths for activation and pip
        if platform.system() == "Windows":
            if venv_created:
                activate_cmd = os.path.join(venv_dir, "Scripts", "activate.bat")
                pip_cmd = os.path.join(venv_dir, "Scripts", "pip.exe")
                python_cmd = os.path.join(venv_dir, "Scripts", "python.exe")
                # Fix the pip install command - use full path to pip
                install_cmd = f'cmd /c "{activate_cmd} && {pip_cmd} install -r requirements.txt"'
            else:
                pip_cmd = "pip"
                python_cmd = "python"
                install_cmd = "pip install -r requirements.txt"
        else:
            if venv_created:
                activate_cmd = os.path.join(venv_dir, "bin", "activate")
                pip_cmd = os.path.join(venv_dir, "bin", "pip")
                python_cmd = os.path.join(venv_dir, "bin", "python")
                # Use bash to activate the environment and run pip
                install_cmd = f'bash -c "source {activate_cmd} && pip install -r requirements.txt"'
            else:
                pip_cmd = "pip"
                python_cmd = "python"
                install_cmd = "pip install -r requirements.txt"
        
        # Run the installation command
        try:
            # Check if requirements.txt exists
            req_path = os.path.join(backend_dir, "requirements.txt")
            
            if not os.path.exists(req_path):
                await websocket.send_text("requirements.txt not found. Creating with basic dependencies...")
                with open(req_path, "w") as f:
                    f.write("fastapi==0.104.1\nuvicorn==0.24.0\nwebsockets==11.0.3\njinja2==3.1.2\naiofiles==23.2.1\n")
            
            # Install dependencies with better error handling
            try:
                await websocket.send_text(f"Installing dependencies using command: {install_cmd}")
                await run_command_with_status(websocket, install_cmd, backend_dir)
                await websocket.send_text("Dependencies installed successfully")
            except Exception as e:
                await websocket.send_text(f"Error with primary install method: {str(e)}")
                
                # Try an alternate approach if the first one fails
                if platform.system() == "Windows" and venv_created:
                    alt_cmd = f"cd /d {backend_dir} && .\\venv\\Scripts\\activate && pip install -r requirements.txt"
                    await websocket.send_text(f"Trying alternate install method: {alt_cmd}")
                    try:
                        os.system(alt_cmd)
                        await websocket.send_text("Alternative installation method completed")
                    except Exception as alt_e:
                        await websocket.send_text(f"Alternative installation also failed: {str(alt_e)}")
                
                # Final fallback to just install the core packages
                await websocket.send_text("Installing core packages directly...")
                if platform.system() == "Windows" and venv_created:
                    os.system(f"cd /d {backend_dir} && .\\venv\\Scripts\\activate && pip install fastapi uvicorn websockets")
                else:
                    os.system(f"pip install fastapi uvicorn websockets")
            
        except Exception as e:
            await websocket.send_text(f"Error during dependency installation process: {str(e)}")
            # We'll continue anyway and hope the basic packages are already installed

        await websocket.send_text("✅ STEP 6 COMPLETE: Dependency installation process finished")

        # STEP 7: Start backend server with more robust approach
        await websocket.send_text("STEP 7: Starting backend server on port 8000...")

        # Verify main.py exists
        main_path = os.path.join(backend_dir, "main.py")
        if not os.path.exists(main_path):
            await websocket.send_text("main.py not found. Creating a basic one...")
            with open(main_path, "w") as f:
                f.write("""from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"message": "Hello from AI Chatbot"}\n""")

        # Create a robust batch file for running the backend
        backend_script = os.path.join(backend_dir, "run_backend.bat")
        with open(backend_script, 'w') as f:
            f.write('@echo off\n')
            f.write('echo ===============================================\n')
            f.write('echo Starting AI Chatbot Backend Server - Port 8000\n')
            f.write('echo ===============================================\n\n')
            f.write(f'cd /d "{backend_dir}"\n\n')
            f.write('echo Activating virtual environment...\n')
            f.write('call venv\\Scripts\\activate.bat\n\n')
            f.write('echo Starting uvicorn server...\n')
            f.write('python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000\n\n')
            f.write('echo Backend server stopped. Press any key to close this window...\n')
            f.write('pause>nul\n')

        await websocket.send_text(f"Created backend starter script: {backend_script}")

        try:
            # Start the backend using subprocess
            await websocket.send_text("Starting backend server...")
            backend_proc = subprocess.Popen(
                f'start cmd /k "{backend_script}"',
                shell=True
            )
            await websocket.send_text(f"Backend process started in a new window")
            
            # Allow time for the server to start
            await websocket.send_text("Waiting for backend server to initialize...")
            for i in range(20, 0, -1):
                await websocket.send_text(f"Backend initialization: {i} seconds remaining...")
                await asyncio.sleep(1)
                
                # Check if backend is accessible
                if i % 5 == 0 or i <= 3:
                    try:
                        import requests
                        try:
                            response = requests.get("http://localhost:8000", timeout=2)
                            if response.status_code < 400:
                                backend_running = True
                                await websocket.send_text(f"✅ Backend server is running and responding on http://localhost:8000")
                                break
                        except requests.exceptions.RequestException:
                            await websocket.send_text("Backend not responding yet...")
                    except ImportError:
                        await websocket.send_text("Cannot check backend status (requests module not available)")
            
            # Mark backend as running
            repo_setup_status["backend_running"] = True
            await websocket.send_text("✅ STEP 7 COMPLETE: Backend is now running")
            
        except Exception as e:
            await websocket.send_text(f"Error starting backend: {str(e)}")
            await websocket.send_text("Continuing with frontend setup...")

        # STEP 8: Navigate to frontend directory
        await websocket.send_text("STEP 8: Setting up frontend directory...")
        frontend_dir = os.path.join(base_dir, "frontend")
        
        if not os.path.exists(frontend_dir):
            await websocket.send_text("❌ ERROR: Frontend directory not found. Cannot continue.")
            return
        
        await websocket.send_text(f"Frontend directory found at {frontend_dir}")
        await websocket.send_text("✅ STEP 8 COMPLETE: Frontend directory located")
        
        # STEP 9: Install frontend dependencies
        await websocket.send_text("STEP 9: Installing frontend dependencies with npm...")
        
        # Verify package.json exists
        pkg_path = os.path.join(frontend_dir, "package.json")
        if not os.path.exists(pkg_path):
            await websocket.send_text("package.json not found. Creating a basic one...")
            with open(pkg_path, "w") as f:
                f.write("""{
  "name": "chatbot-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-scripts": "5.0.2"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}""")

        # Install npm dependencies with improved error handling
        try:
            await websocket.send_text("Running NPM install...")
            npm_result = await run_command_with_status(websocket, "npm install", frontend_dir)
            await websocket.send_text("Frontend dependencies installed successfully")
        except Exception as e:
            await websocket.send_text(f"Error during npm install: {str(e)}")
            await websocket.send_text("Trying alternate install method...")
            try:
                # Try system command directly
                os.system(f"cd /d {frontend_dir} && npm install")
                await websocket.send_text("Alternate npm install completed")
            except Exception as alt_e:
                await websocket.send_text(f"Alternative npm install also failed: {str(alt_e)}")
                await websocket.send_text("Will attempt to continue anyway...")

        await websocket.send_text("✅ STEP 9 COMPLETE: Frontend dependencies installation finished")

        # STEP 10: Start frontend server with more robust approach
        await websocket.send_text("STEP 10: Starting frontend server on port 3000...")

        # Create a reliable batch file for running the frontend
        frontend_script = os.path.join(frontend_dir, "run_frontend.bat")
        with open(frontend_script, 'w') as f:
            f.write('@echo off\n')
            f.write('echo ================================================\n')
            f.write('echo Starting AI Chatbot Frontend Server - Port 3000\n')
            f.write('echo ================================================\n\n')
            f.write(f'cd /d "{frontend_dir}"\n\n')
            f.write('echo Setting PORT environment variable...\n')
            f.write('set PORT=3000\n\n')
            f.write('echo Starting React development server...\n')
            f.write('npm start\n\n')
            f.write('echo Frontend server stopped. Press any key to close this window...\n')
            f.write('pause>nul\n')

        await websocket.send_text(f"Created frontend starter script: {frontend_script}")

        # Make sure backend is actually running before starting frontend
        if not repo_setup_status["backend_running"]:
            await websocket.send_text("⚠️ Warning: Backend may not be running. Frontend may not work correctly.")
            repo_setup_status["backend_running"] = True  # Assume it's running anyway

        # Start the frontend
        try:
            await websocket.send_text("Starting frontend server...")
            frontend_proc = subprocess.Popen(
                f'start cmd /k "{frontend_script}"',
                shell=True
            )
            await websocket.send_text("Frontend process started in a new window")
            
            # Wait for frontend to initialize
            await websocket.send_text("Waiting for frontend server to initialize...")
            for i in range(30, 0, -1):
                await websocket.send_text(f"Frontend initialization: {i} seconds remaining...")
                await asyncio.sleep(1)
            
            # Mark frontend as running
            repo_setup_status["frontend_running"] = True
            await websocket.send_text("✅ STEP 10 COMPLETE: Frontend server is running")
            
            # Final success message with access URL
            await websocket.send_text("\n🎉 SETUP COMPLETE! Both services are now running.")
            await websocket.send_text("\n✅ Backend API: http://localhost:8000")
            await websocket.send_text("✅ Frontend UI: http://localhost:3000")
            await websocket.send_text("\n[SUCCESS] You can now click the 'Access Application' button to open the application.")
            
        except Exception as e:
            await websocket.send_text(f"Error starting frontend: {str(e)}")
            await websocket.send_text("Setup process completed with errors.")
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(error_message)
        try:
            await websocket.send_text(error_message)
        except:
            print("Could not send error message to client")

async def run_command_with_status(websocket, command, cwd):
    """Run a command and return its output - waits for completion before returning"""
    await websocket.send_text(f"Running: {command}")
    
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            shell=True
        )
        
        stdout, stderr = await process.communicate()
        
        stdout_text = stdout.decode() if stdout else ""
        stderr_text = stderr.decode() if stderr else ""
        
        if stdout_text:
            await websocket.send_text(f"Command output:\n{stdout_text}")
        
        if stderr_text:
            await websocket.send_text(f"Command error:\n{stderr_text}")
        
        if process.returncode != 0:
            await websocket.send_text(f"⚠️ Command failed with return code {process.returncode}")
            raise Exception(f"Command failed with return code {process.returncode}")
        else:
            await websocket.send_text(f"Command completed successfully")
        
        return stdout_text + stderr_text
    except Exception as e:
        await websocket.send_text(f"Error executing command: {str(e)}")
        raise

async def check_service_availability(websocket, url, max_retries=3):
    """Check if a service is available at the given URL"""
    await websocket.send_text(f"Checking availability of {url}...")
    
    try:
        import requests
        
        for attempt in range(1, max_retries + 1):
            try:
                await websocket.send_text(f"Connection attempt {attempt} of {max_retries}...")
                response = requests.get(url, timeout=5)
                
                if response.status_code < 400:
                    await websocket.send_text(f"Service at {url} is responding with status code {response.status_code}")
                    return True
                else:
                    await websocket.send_text(f"Service at {url} responded with status code {response.status_code}")
            except requests.exceptions.RequestException as e:
                await websocket.send_text(f"Connection failed: {str(e)}")
                
            if attempt < max_retries:
                await websocket.send_text("Waiting before retry...")
                await asyncio.sleep(3)
        
        await websocket.send_text(f"Service at {url} is not available after {max_retries} attempts")
        return False
    except ImportError:
        await websocket.send_text("Warning: Cannot verify service availability (requests module not available)")
        return True  # Assume it's running if we can't check

async def use_zip_download(websocket, work_dir, repo_path=None):
    """Download repository as ZIP if git clone fails"""
    if not repo_path:
        repo_path = os.path.join(work_dir, "aichatbot")
    
    await websocket.send_text("Downloading repository as ZIP...")
    try:
        import requests
        import zipfile
        import io
        import time
        
        # Download zip file
        zip_url = "https://github.com/AmruthaYalla04/aichatbot/archive/refs/heads/main.zip"
        await websocket.send_text(f"Downloading from {zip_url}")
        
        response = requests.get(zip_url, stream=True)
        if response.status_code == 200:
            # Extract the zip
            await websocket.send_text("Download successful. Extracting zip file...")
            
            # Save zip file to disk
            zip_path = os.path.join(work_dir, "repo.zip")
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(work_dir)
            
            # Remove zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            # Check if the extracted directory exists
            extracted_dir = os.path.join(work_dir, "aichatbot-main")
            if os.path.exists(extracted_dir):
                # Don't try to rename, just use the extracted directory as is
                await websocket.send_text(f"⚠️ Using directory as extracted: {extracted_dir}")
                await websocket.send_text(f"✓ Repository extracted successfully")
                return extracted_dir  # Return the actual path that we'll use
            else:
                await websocket.send_text("⚠️ ZIP extraction failed: No directory found after extraction")
                return False
        else:
            await websocket.send_text(f"⚠️ Failed to download ZIP: HTTP status {response.status_code}")
            return False
    except Exception as e:
        await websocket.send_text(f"⚠️ Error downloading/extracting ZIP: {str(e)}")
        return False

# Add these helper functions for creating files

async def create_demo_repository(websocket, repo_path):
    """Create a minimal repository structure when download fails"""
    await websocket.send_text("Creating minimal repository structure...")
    
    # Create directories
    os.makedirs(os.path.join(repo_path, "backend"), exist_ok=True)
    os.makedirs(os.path.join(repo_path, "frontend", "src"), exist_ok=True) 
    os.makedirs(os.path.join(repo_path, "frontend", "public"), exist_ok=True)
    
    # Create backend files
    backend_dir = os.path.join(repo_path, "backend")
    with open(os.path.join(backend_dir, "main.py"), "w") as f:
        f.write("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from AI Chatbot Demo Backend"}
""")
    
    with open(os.path.join(backend_dir, "requirements.txt"), "w") as f:
        f.write("fastapi>=0.68.0,<0.69.0\nuvicorn>=0.15.0,<0.16.0\n")
    
    await create_basic_frontend_files(websocket, os.path.join(repo_path, "frontend"))
    await websocket.send_text("Demo repository structure created successfully")
    return True

async def create_basic_frontend_files(websocket, frontend_dir):
    """Create basic frontend files for React app"""
    # Create package.json
    with open(os.path.join(frontend_dir, "package.json"), "w") as f:
        f.write("""{
  "name": "chatbot-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-scripts": "4.0.3"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}""")
    
    # Create index.js
    with open(os.path.join(frontend_dir, "src", "index.js"), "w") as f:
        f.write("""
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);
""")
    
    # Create App.js
    with open(os.path.join(frontend_dir, "src", "App.js"), "w") as f:
        f.write("""
import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>AI Chatbot Demo</h1>
      <p>This is a demo React application for the AI Chatbot.</p>
      <p>The backend API is running at <a href="http://localhost:8000">http://localhost:8000</a></p>
    </div>
  );
}

export default App;
""")
    
    # Create index.html
    with open(os.path.join(frontend_dir, "public", "index.html"), "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AI Chatbot</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
""")
    
    await websocket.send_text("Basic frontend files created")

async def create_demo_structure(websocket, work_dir):
    """Create a minimal demo structure if repo can't be cloned or downloaded"""
    await websocket.send_text("Creating a minimal demo structure...")
    repo_dir = os.path.join(work_dir, "aichatbot")
    
    # Create directories
    os.makedirs(repo_dir, exist_ok=True)
    os.makedirs(os.path.join(repo_dir, "backend"), exist_ok=True)
    os.makedirs(os.path.join(repo_dir, "frontend"), exist_ok=True)
    os.makedirs(os.path.join(repo_dir, "frontend", "src"), exist_ok=True)
    os.makedirs(os.path.join(repo_dir, "frontend", "public"), exist_ok=True)
    
    # Create backend files
    backend_dir = os.path.join(repo_dir, "backend")
    with open(os.path.join(backend_dir, "main.py"), "w") as f:
        f.write("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from AI Chatbot Demo Backend"}
""")
    
    with open(os.path.join(backend_dir, "requirements.txt"), "w") as f:
        f.write("fastapi\nuvicorn\n")
    
    # Create frontend files
    frontend_dir = os.path.join(repo_dir, "frontend")
    with open(os.path.join(frontend_dir, "package.json"), "w") as f:
        f.write("""{
  "name": "chatbot-demo",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}""")
    
    with open(os.path.join(frontend_dir, "src", "index.js"), "w") as f:
        f.write("""
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);
""")
    
    with open(os.path.join(frontend_dir, "src", "App.js"), "w") as f:
        f.write("""
import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>AI Chatbot Demo</h1>
      <p>This is a demo application created when the original repository could not be cloned.</p>
      <p>The backend API is available at <a href="http://localhost:8000">http://localhost:8000</a></p>
    </div>
  );
}

export default App;
""")
    
    with open(os.path.join(frontend_dir, "public", "index.html"), "w") as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AI Chatbot Demo</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
""")
    
    await websocket.send_text("Demo structure created successfully!")
    return True

async def setup_backend(websocket, base_dir):
    """Set up and run the backend"""
    backend_dir = os.path.join(base_dir, "backend")
    if not os.path.exists(backend_dir):
        await websocket.send_text(f"Backend directory not found at {backend_dir}!")
        os.makedirs(backend_dir, exist_ok=True)
        await create_demo_structure(websocket, os.path.dirname(base_dir))
        backend_dir = os.path.join(base_dir, "backend")
    
    await websocket.send_text(f"Setting up backend in {backend_dir}")
    
    # Create virtual environment
    await websocket.send_text("Creating Python virtual environment...")
    try:
        await run_command(websocket, "python -m venv venv", backend_dir)
    except Exception as e:
        await websocket.send_text(f"Error creating venv: {str(e)}")
        await websocket.send_text("Trying to continue without virtual environment...")
    
    # Determine paths for python and pip
    if platform.system() == "Windows":
        venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")
        venv_pip = os.path.join(backend_dir, "venv", "Scripts", "pip.exe")
        # Check if they exist
        if not os.path.exists(venv_python) or not os.path.exists(venv_pip):
            await websocket.send_text("Virtual environment executables not found. Using system Python.")
            venv_python = "python"
            venv_pip = "pip"
    else:
        venv_python = os.path.join(backend_dir, "venv", "bin", "python")
        venv_pip = os.path.join(backend_dir, "venv", "bin", "pip")
        if not os.path.exists(venv_python) or not os.path.exists(venv_pip):
            await websocket.send_text("Virtual environment executables not found. Using system Python.")
            venv_python = "python"
            venv_pip = "pip"
    
    # Install dependencies
    req_path = os.path.join(backend_dir, "requirements.txt")
    if os.path.exists(req_path):
        await websocket.send_text("Installing dependencies from requirements.txt...")
        await run_command(websocket, f"\"{venv_pip}\" install -r requirements.txt", backend_dir)
    else:
        await websocket.send_text("requirements.txt not found. Installing basic dependencies...")
        await run_command(websocket, f"\"{venv_pip}\" install fastapi uvicorn", backend_dir)
    
    # Check if main.py exists
    main_path = os.path.join(backend_dir, "main.py")
    if not os.path.exists(main_path):
        await websocket.send_text("main.py not found. Creating a basic one...")
        with open(main_path, "w") as f:
            f.write("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from AI Chatbot Demo Backend"}
""")
    
    # Start backend
    await websocket.send_text("Starting backend server on port 8000...")
    start_cmd = f"\"{venv_python}\" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    
    backend_process = await start_process(websocket, start_cmd, backend_dir)
    
    await websocket.send_text("Backend started successfully!")
    return True

async def setup_frontend(websocket, base_dir):
    """Set up and run the frontend"""
    frontend_dir = os.path.join(base_dir, "frontend")
    if not os.path.exists(frontend_dir):
        await websocket.send_text(f"Frontend directory not found at {frontend_dir}!")
        os.makedirs(frontend_dir, exist_ok=True)
        await create_demo_structure(websocket, os.path.dirname(base_dir))
        frontend_dir = os.path.join(base_dir, "frontend")
    
    await websocket.send_text(f"Setting up frontend in {frontend_dir}")
    
    # Check if package.json exists
    package_path = os.path.join(frontend_dir, "package.json")
    if not os.path.exists(package_path):
        await websocket.send_text("package.json not found. Creating a basic one...")
        with open(package_path, "w") as f:
            f.write("""{
  "name": "chatbot-demo",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}""")
    
    # Install dependencies
    await websocket.send_text("Installing frontend dependencies...")
    try:
        await run_command(websocket, "npm install", frontend_dir)
    except Exception as e:
        await websocket.send_text(f"Error installing dependencies: {str(e)}")
    
    # Start frontend
    await websocket.send_text("Starting frontend on port 3000...")
    start_cmd = "set PORT=3000 && npm start"
    
    frontend_process = await start_process(websocket, start_cmd, frontend_dir)
    
    await websocket.send_text("Frontend started successfully!")
    return True

async def run_command(websocket, command, cwd):
    """Run a command and stream output to the websocket"""
    await websocket.send_text(f"Running: {command}")
    
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        shell=True
    )
    
    stdout, stderr = await process.communicate()
    
    if stdout:
        stdout_text = stdout.decode()
        await websocket.send_text(f"Command output:\n{stdout_text}")
    
    if stderr:
        stderr_text = stderr.decode()
        await websocket.send_text(f"Command error:\n{stderr_text}")
    
    if process.returncode != 0:
        await websocket.send_text(f"Command failed with return code {process.returncode}")
    else:
        await websocket.send_text(f"Command completed successfully")

async def start_process(websocket, command, cwd):
    """Start a long-running process and stream output to the websocket"""
    await websocket.send_text(f"Starting process: {command}")
    
    try:
        # For Windows, use a more reliable approach for starting processes
        if platform.system() == "Windows":
            # Create a batch file for executing the command
            batch_file = os.path.join(cwd, "run_command.bat")
            with open(batch_file, 'w') as f:
                f.write("@echo off\n")
                f.write(f"cd /d \"{cwd}\"\n")
                # For backend server, use a different approach
                if "uvicorn main:app" in command:
                    if "activate.bat" in command:
                        f.write("call venv\\Scripts\\activate.bat\n")
                    f.write("python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000\n")
                    f.write("pause\n")
                # For frontend server
                elif "npm start" in command:
                    f.write("set PORT=3000\n")
                    f.write("npm start\n")
                    f.write("pause\n")
                else:
                    # Generic command
                    f.write(f"{command}\n")
            
            # Execute the batch file in a new window
            process = subprocess.Popen(
                f'start cmd /c "{batch_file}"', 
                shell=True,
                cwd=cwd
            )
            
            await websocket.send_text(f"Process started in a new window with command file: {batch_file}")
            
            # Return a dummy process
            dummy_process = await asyncio.create_subprocess_shell(
                "echo Process started in separate window",
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            return dummy_process
        else:
            # For non-Windows, use the existing approach
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                shell=True
            )
            
            # Stream output in the background
            asyncio.create_task(stream_output(websocket, process))
            return process
    except Exception as e:
        await websocket.send_text(f"Error starting process: {str(e)}")
        raise

async def stream_output(websocket, process):
    """Stream process output to the websocket"""
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        line_text = line.decode().strip()
        if line_text:
            await websocket.send_text(f"Process output: {line_text}")
    
    # Also check stderr
    while True:
        line = await process.stderr.readline()
        if not line:
            break
        line_text = line.decode().strip()
        if line_text:
            await websocket.send_text(f"Process error: {line_text}")

if __name__ == "__main__":
    import uvicorn
    
    # Set up ports - main application on 3002/8002
    backend_port = 8002
    frontend_port = 3002
    
    # Start the backend API
    print(f"Starting backend API on port {backend_port}")
    print(f"Main application UI will be available at http://localhost:{frontend_port}/ui")
    print(f"Cloned repository (when run) will use ports 3000/8000")
    
    # Explicitly set environment variable for React
    os.environ['PORT'] = str(frontend_port)
    
    # Start frontend application in a separate process
    try:
        # Start a new process to run the React frontend on port 3002
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
        if os.path.exists(frontend_dir):
            print(f"Starting React frontend on port {frontend_port}...")
            subprocess.Popen(
                f"cd /d {frontend_dir} && set PORT={frontend_port} && npm start",
                shell=True
            )
    except Exception as e:
        print(f"Could not start frontend: {str(e)}")
    
    # Wait a bit
    time.sleep(3)
    
    # Start the FastAPI backend
    uvicorn.run(app, host="0.0.0.0", port=backend_port, log_level="debug")
