"""
Script to start only the backend server
"""

import os
import sys
import importlib.util
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.setup_db import setup_database

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Setup database
    print("Setting up database...")
    setup_database()
    
    # Run backend
    print("Starting backend server...")
    
    # Get the absolute path to the backend app.py
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    backend_app_path = os.path.join(backend_dir, "app.py")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Add backend directory to path
    sys.path.insert(0, backend_dir)
    
    # Import the Flask app using importlib to avoid naming conflicts
    spec = importlib.util.spec_from_file_location("backend_app", backend_app_path)
    backend_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend_module)
    
    # Get the Flask app instance
    app = backend_module.app
    
    # Run the Flask app
    port = int(os.getenv("PORT", 5000))
    print(f"Backend server running on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    # Disable debug mode to prevent auto-reloading issues
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max request size
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True) 