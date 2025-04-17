import os
import sys
import subprocess
import time
import threading
import argparse
import webbrowser
from dotenv import load_dotenv
import socket

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.setup_db import setup_database
from utils.rasa_integration import RasaIntegration

def check_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_backend():
    """Run the Flask backend server"""
    try:
        # Navigate to the backend directory and run Flask
        backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
        os.chdir(backend_path)
        
        # Use subprocess to run Flask
        subprocess.run(["python", "app.py"])
    except Exception as e:
        print(f"Error starting backend server: {e}")
        print("Make sure you have installed all dependencies with 'pip install -r requirements.txt'")

def run_frontend():
    """Run the Streamlit frontend"""
    try:
        # Navigate to the frontend directory and run Streamlit
        frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
        os.chdir(frontend_path)
        
        # Use subprocess to run Streamlit
        subprocess.run(["streamlit", "run", "app.py"])
    except Exception as e:
        print(f"Error starting frontend server: {e}")
        print("Make sure you have installed all dependencies with 'pip install -r requirements.txt'")

def run_rasa_bot():
    """Run the Rasa chatbot"""
    try:
        # Use the RasaIntegration class to start the Rasa servers
        rasa_integration = RasaIntegration()
        
        print("Starting Rasa servers...")
        rasa_server_process, action_server_process = rasa_integration.start_rasa_servers()
        
        print("Rasa chatbot started on:")
        print("- Rasa server: http://localhost:5005")
        print("- Action server: http://localhost:5055")
        
        # Keep the processes alive
        try:
            while True:
                time.sleep(1)
                
                # Check if processes are still running
                if rasa_server_process.poll() is not None:
                    print("Rasa server stopped unexpectedly. Restarting...")
                    rasa_server_process = subprocess.Popen(
                        ["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                
                if action_server_process.poll() is not None:
                    print("Action server stopped unexpectedly. Restarting...")
                    action_server_process = subprocess.Popen(
                        ["rasa", "run", "actions", "--port", "5055"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
        except KeyboardInterrupt:
            # Terminate processes on interrupt
            if rasa_server_process:
                rasa_server_process.terminate()
            if action_server_process:
                action_server_process.terminate()
            
            print("Rasa servers stopped.")
    except Exception as e:
        print(f"Error starting Rasa bot: {e}")
        print("Make sure Rasa is installed correctly with 'pip install -r requirements.txt'")

def check_postgresql_connection():
    """Check if PostgreSQL connection is working"""
    try:
        from sqlalchemy import create_engine
        
        # Get PostgreSQL connection string
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("Error: DATABASE_URL environment variable not set")
            return False
            
        if not db_url.startswith("postgresql://"):
            print("Error: DATABASE_URL should be a PostgreSQL connection string")
            return False
        
        # Try to connect to PostgreSQL
        engine = create_engine(db_url)
        connection = engine.connect()
        connection.close()
        
        print("PostgreSQL connection successful!")
        return True
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        print("Make sure PostgreSQL is running and the connection string is correct")
        return False

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Run the AI Chatbot application with Rasa and PostgreSQL")
    parser.add_argument("--backend-only", action="store_true", help="Run only the backend server")
    parser.add_argument("--frontend-only", action="store_true", help="Run only the frontend server")
    parser.add_argument("--rasa-only", action="store_true", help="Run only the Rasa bot")
    parser.add_argument("--no-rasa", action="store_true", help="Skip starting the Rasa bot")
    parser.add_argument("--no-setup", action="store_true", help="Skip database setup")
    parser.add_argument("--port", type=int, default=5000, help="Port for the backend server")
    parser.add_argument("--frontend-port", type=int, default=8501, help="Port for the Streamlit frontend")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check PostgreSQL connection
    if not check_postgresql_connection():
        print("Failed to connect to PostgreSQL. Exiting.")
        return
    
    # Check if ports are already in use
    if not args.frontend_only and not args.rasa_only and check_port_in_use(args.port):
        print(f"Warning: Port {args.port} is already in use. Backend may not start correctly.")
        print(f"Try using a different port with: python app.py --port {args.port + 1}")
    
    if not args.backend_only and not args.rasa_only and check_port_in_use(args.frontend_port):
        print(f"Warning: Port {args.frontend_port} is already in use. Frontend may not start correctly.")
        print(f"Try using a different port with: python app.py --frontend-port {args.frontend_port + 1}")
    
    if not args.backend_only and not args.frontend_only and not args.no_rasa:
        if check_port_in_use(5005):
            print("Warning: Port 5005 is already in use. Rasa server may not start correctly.")
        if check_port_in_use(5055):
            print("Warning: Port 5055 is already in use. Rasa Action server may not start correctly.")
    
    # Set environment variables for ports
    os.environ["PORT"] = str(args.port)
    os.environ["STREAMLIT_SERVER_PORT"] = str(args.frontend_port)
    os.environ["API_URL"] = f"http://localhost:{args.port}/api"
    
    # Setup database if not skipped
    if not args.no_setup:
        try:
            print("Setting up database...")
            setup_database()
        except Exception as e:
            print(f"Error setting up database: {e}")
            print("Continuing with application startup...")
    
    # Determine what to run
    run_backend_server = not args.frontend_only and not args.rasa_only
    run_frontend_server = not args.backend_only and not args.rasa_only
    run_rasa_server = not args.backend_only and not args.frontend_only and not args.no_rasa or args.rasa_only
    
    # Print startup instructions
    print("\n============== AI CHATBOT SYSTEM ==============")
    print("Make sure you have installed all dependencies:")
    print("pip install -r requirements.txt")
    print("\nDefault user credentials:")
    print("Username: admin")
    print("Password: password123")
    print("==============================================\n")
    
    # Start the backend server in a separate thread if needed
    if run_backend_server:
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        print(f"Backend server starting on http://localhost:{args.port}")
        
        # Wait a bit for the backend to start
        time.sleep(2)
    
    # Start the Rasa bot in a separate thread if needed
    if run_rasa_server:
        rasa_thread = threading.Thread(target=run_rasa_bot)
        rasa_thread.daemon = True
        rasa_thread.start()
        print("Rasa chatbot starting...")
        
        # Wait a bit for the Rasa bot to start
        time.sleep(3)
    
    # Start the frontend server if needed
    if run_frontend_server:
        print(f"Frontend server starting on http://localhost:{args.frontend_port}")
        
        # Open browser
        try:
            webbrowser.open(f"http://localhost:{args.frontend_port}")
        except:
            print(f"Could not open browser automatically. Please navigate to: http://localhost:{args.frontend_port}")
        
        # Run frontend (this will block until frontend is stopped)
        run_frontend()
    elif run_backend_server or (run_rasa_server and not args.frontend_only):
        # If only running backend or Rasa, keep the main thread alive
        print("Press Ctrl+C to stop the server")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
    
    print("Application stopped")

if __name__ == "__main__":
    main() 