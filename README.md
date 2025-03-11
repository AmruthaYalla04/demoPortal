# GitHub Repository Runner

This application allows you to clone and run the AI Chatbot repository with a single click. It handles all the necessary setup, including:

1. Cloning the repository
2. Setting up the backend environment
3. Installing backend dependencies
4. Starting the backend server
5. Setting up the frontend environment
6. Installing frontend dependencies
7. Starting the frontend server

## Prerequisites

- Git
- Python 3.8+ (with venv support)
- Node.js and npm
- Bash (Git Bash for Windows users)

## Port Configuration

The application uses the following port structure:
- **Main application**: 
  - Frontend UI: http://localhost:3002
  - Backend API: http://localhost:8002
- **Cloned repository**: 
  - Frontend: http://localhost:3000
  - Backend: http://localhost:8000

## Running the application

### Main Application

1. Start the main application:

```
python main.py
```

This will automatically:
- Start the backend server on port 8002
- Start the main application UI on port 3002

2. Open your browser and go to http://localhost:3002
3. Click the "Run Repository" button to start the setup process
4. Once setup is complete, the "Access Application" button will be enabled
5. Click "Access Application" to open the AI Chatbot application in a new tab (http://localhost:3000)

### Manual Setup (Alternative)

If you prefer to run the services individually:

#### Backend setup

1. Navigate to the backend directory:
```
cd backend
```

2. Create a virtual environment:
```
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```
pip install -r requirements.txt
```

5. Start the backend server:
```
uvicorn main:app --reload --port 8002
```

#### Frontend setup

1. Navigate to the frontend directory:
```
cd frontend
```

2. Install dependencies:
```
npm install
```

3. Start the frontend:
```
npm start
```

## Using the Command Script

You can also run the entire setup process using the shell script:

```
bash run_commands.sh
```

This script will:
1. Clone the repository
2. Set up the backend and frontend environments
3. Start both services

The script consolidates all necessary commands in a single file for easy execution.
