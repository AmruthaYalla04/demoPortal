"""
Launcher script to start the GitHub Repository Runner application.
This script will redirect to the merged backend/main.py file.
"""
import os
import sys
import subprocess

def main():
    """Launch the merged application by redirecting to backend/main.py"""
    print("=====================================================")
    print("     GitHub Repository Runner - Launcher")
    print("=====================================================")
    print("Starting the application with merged backend/frontend...")
    print()
    print("PORTS:")
    print("  - Main application: Frontend 3002, Backend 8002")
    print("  - Cloned repository (when run): Frontend 3000, Backend 8000")
    print()
    
    # Path to the backend main.py
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    backend_main = os.path.join(backend_dir, "main.py")
    
    if not os.path.exists(backend_main):
        print(f"ERROR: Backend main.py not found at {backend_main}")
        print("Make sure you've set up the project correctly.")
        return 1
    
    # Execute the backend main.py
    print(f"Launching application from {backend_main}...")
    print(f"You can access the UI at http://localhost:3002/ui")
    print()
    
    # Run the backend main.py directly
    os.chdir(backend_dir)
    os.execl(sys.executable, sys.executable, "main.py")

if __name__ == "__main__":
    sys.exit(main())
