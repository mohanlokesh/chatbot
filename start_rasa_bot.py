"""
Script to start the Rasa chatbot with PostgreSQL integration
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.rasa_integration import RasaIntegration

def check_postgresql_connection():
    """Check if PostgreSQL connection is working"""
    try:
        # Get database URL from environment variable
        print("Checking PostgreSQL connection...")
        from sqlalchemy import create_engine
        
        # Load environment variables
        load_dotenv()
        
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
    """Main entry point for the Rasa bot startup"""
    parser = argparse.ArgumentParser(description="Start the Rasa chatbot with PostgreSQL integration")
    parser.add_argument("--train", action="store_true", help="Train the Rasa model before starting")
    parser.add_argument("--skip-seed", action="store_true", help="Skip seeding Rasa with database examples")
    parser.add_argument("--seed-only", action="store_true", help="Only seed Rasa with database examples without starting the server")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check PostgreSQL connection
    if not check_postgresql_connection():
        print("Failed to connect to PostgreSQL. Exiting.")
        return
    
    # Initialize Rasa integration
    rasa_integration = RasaIntegration()
    
    # Seed Rasa with database examples
    if not args.skip_seed:
        print("Seeding Rasa with database examples...")
        rasa_integration.seed_rasa_from_database()
    
    # Train Rasa model if requested
    if args.train:
        print("Training Rasa model...")
        success = rasa_integration.train_rasa_model()
        if not success:
            print("Failed to train Rasa model. Exiting.")
            return
    
    # Exit if only seeding was requested
    if args.seed_only:
        print("Seeding completed.")
        return
    
    # Start Rasa servers
    try:
        print("Starting Rasa servers...")
        rasa_server_process, action_server_process = rasa_integration.start_rasa_servers()
        
        print("\n=========================================")
        print("Rasa chatbot is now running!")
        print("Rasa server: http://localhost:5005")
        print("Action server: http://localhost:5055")
        print("=========================================\n")
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down Rasa servers...")
            
            # Terminate processes
            if rasa_server_process:
                rasa_server_process.terminate()
            if action_server_process:
                action_server_process.terminate()
            
            print("Rasa servers stopped.")
    
    except Exception as e:
        print(f"Error starting Rasa servers: {e}")
        print("Make sure you have installed Rasa and its dependencies with 'pip install -r requirements.txt'")

if __name__ == "__main__":
    main() 