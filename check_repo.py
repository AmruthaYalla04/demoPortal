"""
Utility to check the structure of the repository
"""
import os
import requests
import time
import webbrowser
import sys

def check_ports():
    """Check if required ports are available"""
    ports = [3002, 8002, 3000, 8000]
    issues = []
    
    for port in ports:
        try:
            # Try to connect to the port
            response = requests.get(f"http://localhost:{port}", timeout=0.5)
            issues.append(f"Port {port} is already in use")
        except requests.exceptions.ConnectionError:
            print(f"Port {port} is available")
        except Exception as e:
            print(f"Error checking port {port}: {str(e)}")
    
    return issues

def check_repository(repo_url="https://github.com/AmruthaYalla04/aichatbot.git"):
    """Check if repository can be cloned and if it has the expected structure"""
    import tempfile
    import subprocess
    import shutil
    
    print(f"Checking repository: {repo_url}")
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Try to clone the repository
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"Failed to clone repository: {result.stderr}")
            return False
        
        # Check structure
        chatbot_dir = os.path.join(temp_dir, "chatbot")
        if os.path.isdir(chatbot_dir):
            print("Found 'chatbot' directory")
            backend_dir = os.path.join(chatbot_dir, "backend")
            frontend_dir = os.path.join(chatbot_dir, "frontend")
        else:
            print("Warning: 'chatbot' directory not found, checking root")
            backend_dir = os.path.join(temp_dir, "backend")
            frontend_dir = os.path.join(temp_dir, "frontend")
        
        issues = []
        
        # Check backend
        if not os.path.isdir(backend_dir):
            issues.append("Backend directory not found")
        else:
            print("Backend directory found")
            if not os.path.isfile(os.path.join(backend_dir, "main.py")):
                issues.append("Backend main.py not found")
            else:
                print("Backend main.py found")
            
            if not os.path.isfile(os.path.join(backend_dir, "requirements.txt")):
                issues.append("Backend requirements.txt not found")
            else:
                print("Backend requirements.txt found")
        
        # Check frontend
        if not os.path.isdir(frontend_dir):
            issues.append("Frontend directory not found")
        else:
            print("Frontend directory found")
            if not os.path.isfile(os.path.join(frontend_dir, "package.json")):
                issues.append("Frontend package.json not found")
            else:
                print("Frontend package.json found")
        
        if issues:
            print("\nIssues found with repository:")
            for issue in issues:
                print(f"- {issue}")
            return False
        else:
            print("\nRepository structure looks good!")
            return True
            
    except Exception as e:
        print(f"Error checking repository: {str(e)}")
        return False
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")

def check_installations():
    """Check if required software is installed"""
    import shutil
    
    issues = []
    
    # Check Git
    if shutil.which("git") is None:
        issues.append("Git is not installed or not in PATH")
    else:
        print("Git is installed")
    
    # Check Python
    if shutil.which("python") is None:
        issues.append("Python is not installed or not in PATH")
    else:
        print("Python is installed")
    
    # Check Node.js
    if shutil.which("node") is None:
        issues.append("Node.js is not installed or not in PATH")
    else:
        print("Node.js is installed")
    
    # Check npm
    if shutil.which("npm") is None:
        issues.append("npm is not installed or not in PATH")
    else:
        print("npm is installed")
    
    return issues

def main():
    print("=====================================================")
    print("     GitHub Repository Runner - System Check         ")
    print("=====================================================")
    
    # Check installations
    print("\nChecking required software installations:")
    install_issues = check_installations()
    
    # Check ports
    print("\nChecking if required ports are available:")
    port_issues = check_ports()
    
    # Check repository
    print("\nChecking repository structure:")
    repo_check = check_repository()
    
    # Summary
    print("\n=====================================================")
    print("                    Summary                         ")
    print("=====================================================")
    
    if install_issues:
        print("\n❌ Software installation issues found:")
        for issue in install_issues:
            print(f"- {issue}")
    else:
        print("\n✅ All required software is installed")
    
    if port_issues:
        print("\n❌ Port issues found:")
        for issue in port_issues:
            print(f"- {issue}")
    else:
        print("\n✅ All required ports are available")
    
    if repo_check:
        print("\n✅ Repository structure is valid")
    else:
        print("\n❌ Repository structure has issues")
    
    print("\n=====================================================")
    
    if install_issues or port_issues or not repo_check:
        print("Please fix the issues above before running the application.")
        return 1
    else:
        print("All checks passed! You can run the application.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
