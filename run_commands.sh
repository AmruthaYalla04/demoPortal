#!/bin/bash

# Display title and information
echo "======================================================="
echo "     GitHub Repository Runner - Command Script         "
echo "======================================================="
echo "This script will clone and run the AI Chatbot repository"
echo "PORTS:"
echo "  - Main application: Frontend 3002, Backend 8002"
echo "  - Cloned repository: Frontend 3000, Backend 8000"
echo "======================================================="
echo ""

# Working directory for cloned repos
WORK_DIR="$(pwd)/cloned_repos"
mkdir -p "$WORK_DIR"
echo "[$(date +%T)] Created working directory: $WORK_DIR"

# Clean up existing repository if exists
if [ -d "$WORK_DIR/aichatbot" ]; then
  echo "[$(date +%T)] Removing existing repository..."
  rm -rf "$WORK_DIR/aichatbot"
fi

# Clone the repository
echo "[$(date +%T)] Cloning repository: https://github.com/AmruthaYalla04/aichatbot.git"
git clone https://github.com/AmruthaYalla04/aichatbot.git "$WORK_DIR/aichatbot"

# Check if clone was successful
if [ ! -d "$WORK_DIR/aichatbot" ]; then
  echo "[$(date +%T)] ERROR: Clone failed. Exiting script."
  exit 1
fi

echo "[$(date +%T)] Repository cloned successfully."

# Navigate to chatbot directory (if it exists)
if [ -d "$WORK_DIR/aichatbot/chatbot" ]; then
  echo "[$(date +%T)] Found 'chatbot' directory, navigating..."
  cd "$WORK_DIR/aichatbot/chatbot"
else
  echo "[$(date +%T)] Warning: 'chatbot' directory not found, using repository root."
  cd "$WORK_DIR/aichatbot"
fi

# Navigate to backend directory
echo "[$(date +%T)] Navigating to backend directory..."
if [ ! -d "backend" ]; then
  echo "[$(date +%T)] ERROR: Backend directory not found!"
  exit 1
fi
cd backend

# Create virtual environment
echo "[$(date +%T)] Setting up backend environment..."
echo "[$(date +%T)] Creating Python virtual environment..."
python -m venv venv

# Activate the virtual environment based on OS
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
  # Windows
  echo "[$(date +%T)] Activating virtual environment on Windows..."
  source venv/Scripts/activate
else
  # Linux/Mac
  echo "[$(date +%T)] Activating virtual environment on Unix-based OS..."
  source venv/bin/activate
fi

# Install backend dependencies
echo "[$(date +%T)] Installing backend dependencies..."
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  echo "[$(date +%T)] Warning: requirements.txt not found. Installing basic dependencies..."
  pip install fastapi uvicorn
fi

# Start backend server in background
echo "[$(date +%T)] Starting backend server on port 8000..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "[$(date +%T)] Backend server started with PID: $BACKEND_PID"

# Wait for backend to start
echo "[$(date +%T)] Waiting for backend to initialize (10 seconds)..."
sleep 10

# Navigate to frontend directory
echo "[$(date +%T)] Navigating to frontend directory..."
cd .. || { echo "[$(date +%T)] ERROR: Cannot navigate up from backend directory!"; exit 1; }

if [ ! -d "frontend" ]; then
  echo "[$(date +%T)] ERROR: Frontend directory not found!"
  exit 1
fi
cd frontend

echo "[$(date +%T)] Setting up frontend environment..."

# Install frontend dependencies
echo "[$(date +%T)] Installing frontend dependencies with npm..."
npm install

# Start frontend server
echo "[$(date +%T)] Starting frontend server on port 3000..."
PORT=3000 npm start &
FRONTEND_PID=$!
echo "[$(date +%T)] Frontend server started with PID: $FRONTEND_PID"

# Print success message
echo ""
echo "======================================================="
echo "          APPLICATION SETUP COMPLETE!                  "
echo "======================================================="
echo "Backend is running at: http://localhost:8000"
echo "Frontend is running at: http://localhost:3000"
echo ""
echo "To access the application, open your browser and go to:"
echo "http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the servers"
echo "======================================================="

# Keep script running to maintain child processes
wait
