import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isSetupComplete, setIsSetupComplete] = useState(false);
  const websocketRef = useRef(null);
  const logEndRef = useRef(null);

  // Scroll to bottom of logs when they update
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Close websocket on component unmount
  useEffect(() => {
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);

  // More aggressive polling for setup status
  useEffect(() => {
    if (isRunning) {
      const statusInterval = setInterval(() => {
        fetch('http://localhost:8002/status')
          .then(response => response.json())
          .then(data => {
            if (data.backend_running && data.frontend_running) {
              setIsSetupComplete(true);
              clearInterval(statusInterval);
              addLog("[SUCCESS] Setup complete! You can now access the application.");
            }
          })
          .catch(error => {
            console.error('Error checking status:', error);
          });
      }, 3000); // Check every 3 seconds (more frequent)
      
      return () => clearInterval(statusInterval);
    }
  }, [isRunning]);

  // More clearly show the repository command execution flow in logs
  const runRepository = () => {
    setIsRunning(true);
    setLogs([
      `Starting GitHub Repository Runner...`,
      `Repository: https://github.com/AmruthaYalla04/aichatbot.git`,
      `Main app running on ports 3002/8002`,
      `Cloned app will run on ports 3000/8000`,
      `Connecting to server at ws://localhost:8002/ws/run-repo...`
    ]);
    setIsSetupComplete(false);

    // Close existing connection if there is one
    if (websocketRef.current) {
      websocketRef.current.close();
    }

    // Add a timeout to ensure the backend is ready
    setTimeout(() => {
      try {
        // Test server availability first
        fetch('http://localhost:8002/')
          .then(response => {
            if (response.ok) {
              addLog('Backend server is available, connecting to WebSocket...');
              // Connect to the WebSocket
              const ws = new WebSocket('ws://localhost:8002/ws/run-repo');
              websocketRef.current = ws;
              
              ws.onopen = () => {
                setIsConnected(true);
                addLog('✅ Connected to server successfully');
              };
          
              ws.onmessage = (event) => {
                addLog(event.data);
              };
          
              ws.onclose = () => {
                setIsConnected(false);
                addLog('Connection closed');
                // Only set isRunning to false if setup isn't complete
                if (!isSetupComplete) {
                  setIsRunning(false);
                }
              };
          
              ws.onerror = (error) => {
                setIsConnected(false);
                addLog(`WebSocket Error: ${error.message || 'Connection failed'}`);
                addLog('Please make sure the backend server is running on port 8002');
                setIsRunning(false);
              };
            } else {
              throw new Error(`Server responded with status: ${response.status}`);
            }
          })
          .catch(error => {
            addLog(`Error connecting to server: ${error.message}`);
            addLog('Please make sure the backend server is running on port 8002');
            addLog('Try restarting the application by running: python main.py');
            setIsRunning(false);
          });
      } catch (error) {
        addLog(`Error: ${error.message}`);
        setIsRunning(false);
      }
    }, 1000); // Wait 1 second before connecting
  };

  const executeScript = async () => {
    try {
      addLog("Starting command execution in separate window...");
      const response = await fetch('http://localhost:8002/execute-script', {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        addLog(`Script execution initiated: ${data.message}`);
        addLog("This will open a new command window to run the repository.");
        addLog("Please follow the instructions in the command window.");
      } else {
        throw new Error(`Server responded with status: ${response.status}`);
      }
    } catch (error) {
      addLog(`Error executing script: ${error.message}`);
      addLog("Trying alternative method...");
      
      // Try to open the batch file directly as a fallback
      try {
        window.open('run_commands.bat', '_blank');
        addLog("Opened run_commands.bat directly. Check your taskbar for the command window.");
      } catch (e) {
        addLog("Could not open script directly. Please run run_commands.bat manually.");
      }
    }
  };

  const addLog = (message) => {
    setLogs(prevLogs => [...prevLogs, message]);
  };

  const accessApplication = () => {
    // Show loading message
    addLog("Opening AI Chatbot application...");
    
    // First try to check if the application is actually ready
    fetch('http://localhost:3000')
      .then(response => {
        // Application is responding, open it
        window.open('http://localhost:3000', '_blank');
        addLog("✅ Application opened in new tab");
      })
      .catch(error => {
        console.error('Error checking application availability:', error);
        // Try to open it anyway, but with a warning
        addLog("⚠️ Could not verify if application is running. Opening anyway...");
        window.open('http://localhost:3000', '_blank');
        
        // Show more detailed help if there's an issue
        setTimeout(() => {
          addLog("If the application doesn't load correctly:");
          addLog("1. Make sure both backend and frontend windows are still open");
          addLog("2. Check that backend is running on port 8000");
          addLog("3. Check that frontend is running on port 3000");
          addLog("4. Try refreshing the application tab after a few seconds");
        }, 2000);
      });
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>GitHub Repository Runner</h1>
        <p>Run the AI Chatbot repository with one click</p>
        
        <div className="control-panel">
          <button 
            onClick={runRepository} 
            disabled={isRunning || isSetupComplete}
            className="run-button"
          >
            {isRunning ? 'Running...' : isSetupComplete ? 'Setup Complete' : 'Run Repository'}
          </button>
          
          {isConnected && !isSetupComplete && (
            <div className="connection-status connected">
              Connected to server
            </div>
          )}
          
          {isSetupComplete && (
            <div className="success-panel">
              <div className="success-message">
                [SUCCESS] Repository setup successful!
              </div>
              
              <button 
                onClick={executeScript} 
                className="script-button"
              >
                Run All Commands in CMD
              </button>
              
              <button 
                onClick={accessApplication} 
                className="access-button"
              >
                Access Application
              </button>
            </div>
          )}
        </div>

        <div className="log-container">
          <h3>Command Output:</h3>
          <div className="logs">
            {logs.map((log, index) => (
              <div key={index} className="log-line">
                {log}
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      </header>
    </div>
  );
}

export default App;
