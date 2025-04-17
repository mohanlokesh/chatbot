"""
Script to start only the frontend server
"""

import os
import sys
import subprocess
import webbrowser
import requests
import time
from dotenv import load_dotenv

def check_backend_connection(api_url, max_retries=3, retry_delay=2):
    """Check if the backend server is running and accessible"""
    print(f"Checking backend connection at {api_url}...")
    
    for i in range(max_retries):
        try:
            # Make a simple request to the backend
            response = requests.get(api_url.replace('/api', ''), timeout=5)
            if response.status_code == 200 or response.status_code == 404:
                # 404 is also acceptable as it means the server is running but the endpoint doesn't exist
                print("✓ Backend server is running!")
                return True
        except requests.exceptions.RequestException:
            print(f"✗ Backend connection attempt {i+1}/{max_retries} failed.")
            if i < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    print("\n⚠️ Warning: Could not connect to the backend server!")
    print("Your chatbot may not work properly without the backend running.")
    print(f"Please make sure the backend is running at: {api_url}")
    print("You can start it with: python start_backend.py\n")
    
    while True:
        choice = input("Do you want to continue anyway? (y/n): ").lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        else:
            print("Please enter 'y' or 'n'")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Make sure API_URL is set
    port = int(os.getenv("PORT", 5000))
    api_url = os.getenv("API_URL", f"http://localhost:{port}/api")
    os.environ["API_URL"] = api_url
    
    print("\n============== AI CHATBOT FRONTEND ==============")
    print("Backend API URL:", api_url)
    print("\nDefault user credentials:")
    print("Username: admin")
    print("Password: password123")
    print("================================================\n")
    
    # Check backend connection
    if not check_backend_connection(api_url):
        print("Exiting...")
        sys.exit(1)
    
    # Navigate to the frontend directory
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    os.chdir(frontend_path)
    
    # Get frontend port
    frontend_port = int(os.getenv("STREAMLIT_SERVER_PORT", 8501))
    
    # Try to open browser
    try:
        webbrowser.open(f"http://localhost:{frontend_port}")
    except:
        print(f"Could not open browser automatically. Please navigate to: http://localhost:{frontend_port}")
    
    # Run streamlit
    print(f"Starting frontend on http://localhost:{frontend_port}")
    print("Press Ctrl+C to stop")
    
    try:
        subprocess.run(["streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("Shutting down frontend...")
    except Exception as e:
        print(f"Error starting frontend: {e}")
        print("Make sure you have installed all dependencies with 'pip install -r requirements.txt'") 