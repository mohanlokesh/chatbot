"""
Module for integrating Rasa with our existing chatbot system
"""

import os
import sys
import json
import requests
import subprocess
import threading
import time
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import SupportData, Message, Conversation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class RasaIntegration:
    """Class to handle integration between Rasa and our existing chatbot"""
    
    def __init__(self, db_url=None):
        """Initialize RasaIntegration with database connection"""
        # Set up database connection
        if not db_url:
            # Get the absolute project root path
            PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Use absolute path for the SQLite database file
            db_url = os.getenv("DATABASE_URL")
            if not db_url or db_url.startswith("sqlite:///"):
                DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
                db_url = f"sqlite:///{DB_PATH}"
        
        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Rasa server URLs
        self.rasa_url = os.getenv("RASA_URL", "http://localhost:5005")
        
        # Rasa paths
        self.rasa_bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rasa_bot")
        
        # Fallback options
        self.fallbacks = [
            "I'm sorry, I don't have information about that topic. I can help with questions about orders, shipping, returns, and using our website.",
            "I don't have enough information to answer that. I specialize in customer support for our online store. Is there something about your order I can help with?",
            "That's outside my area of expertise. I can assist with orders, returns, shipping, and account questions. How can I help you with one of those?",
            "I'm not able to provide information on that topic. Would you like help with something related to our store, like placing an order or tracking a package?"
        ]
    
    def start_rasa_servers(self):
        """Start Rasa server and action server in separate processes"""
        print("Starting Rasa servers...")
        
        # Change to the rasa bot directory
        os.chdir(self.rasa_bot_dir)
        
        # Start Rasa action server
        action_server_cmd = ["rasa", "run", "actions", "--port", "5055"]
        action_server_process = subprocess.Popen(
            action_server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Rasa Action Server starting on port 5055...")
        
        # Allow action server time to start
        time.sleep(3)
        
        # Start Rasa server
        rasa_server_cmd = ["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005"]
        rasa_server_process = subprocess.Popen(
            rasa_server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Rasa Server starting on port 5005...")
        
        # Wait a bit for servers to initialize
        time.sleep(5)
        
        return rasa_server_process, action_server_process
    
    def train_rasa_model(self):
        """Train the Rasa model"""
        print("Training Rasa model...")
        
        # Change to the rasa bot directory
        os.chdir(self.rasa_bot_dir)
        
        # Run training command
        result = subprocess.run(
            ["rasa", "train"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            print("Rasa model trained successfully!")
            return True
        else:
            print(f"Error training Rasa model: {result.stderr}")
            return False
    
    def seed_rasa_from_database(self):
        """Seed Rasa NLU data with examples from our database"""
        session = self.Session()
        
        try:
            # Get support data from database
            support_data = session.query(SupportData).all()
            
            if not support_data:
                print("No support data found in database")
                return False
            
            # Create NLU data directory if it doesn't exist
            nlu_dir = os.path.join(self.rasa_bot_dir, "data", "nlu")
            os.makedirs(nlu_dir, exist_ok=True)
            
            # Create a new NLU file for database examples
            nlu_file = os.path.join(nlu_dir, "database_examples.yml")
            
            # Group questions by categories
            categories = {}
            for item in support_data:
                category = item.category or "general"
                if category not in categories:
                    categories[category] = []
                categories[category].append(item.question)
            
            # Write to YML file
            with open(nlu_file, "w") as f:
                f.write("version: \"3.1\"\n\n")
                f.write("nlu:\n")
                
                for category, questions in categories.items():
                    intent_name = f"ask_{category.lower().replace(' ', '_')}"
                    f.write(f"- intent: {intent_name}\n")
                    f.write("  examples: |\n")
                    
                    for question in questions:
                        # Clean up the question and add it as an example
                        clean_question = question.strip().replace("\n", " ")
                        f.write(f"    - {clean_question}\n")
                    
                    f.write("\n")
            
            print(f"Created NLU training data at {nlu_file}")
            return True
            
        finally:
            session.close()
    
    def process_message(self, message_text, user_id, conversation_id=None):
        """
        Process a message using Rasa
        
        Args:
            message_text (str): The user's message
            user_id (int): The user's ID
            conversation_id (int, optional): The conversation ID
            
        Returns:
            dict: Response with text and metadata
        """
        session = self.Session()
        
        try:
            # Create new conversation if needed
            if not conversation_id:
                conversation = Conversation(user_id=user_id)
                session.add(conversation)
                session.commit()
                conversation_id = conversation.id
            else:
                conversation = session.query(Conversation).get(conversation_id)
            
            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                is_user=True,
                content=message_text
            )
            session.add(user_message)
            session.commit()
            
            # Send message to Rasa
            try:
                rasa_response = self.send_to_rasa(message_text, conversation_id)
                if rasa_response and "text" in rasa_response:
                    response_text = rasa_response["text"]
                else:
                    # Fallback if Rasa doesn't return a valid response
                    import random
                    response_text = random.choice(self.fallbacks)
            except Exception as e:
                print(f"Error sending message to Rasa: {e}")
                import random
                response_text = random.choice(self.fallbacks)
            
            # Save bot response
            bot_message = Message(
                conversation_id=conversation_id,
                is_user=False,
                content=response_text
            )
            session.add(bot_message)
            session.commit()
            
            return {
                'text': response_text,
                'conversation_id': conversation_id,
                'message_id': bot_message.id
            }
            
        finally:
            session.close()
    
    def send_to_rasa(self, message_text, conversation_id=None):
        """
        Send a message to the Rasa server
        
        Args:
            message_text (str): The message to send
            conversation_id (int, optional): The conversation ID
            
        Returns:
            dict: The Rasa response
        """
        sender_id = f"user_{conversation_id}" if conversation_id else "new_user"
        
        try:
            # Send message to Rasa
            response = requests.post(
                f"{self.rasa_url}/webhooks/rest/webhook",
                json={"sender": sender_id, "message": message_text}
            )
            
            if response.status_code == 200:
                # Rasa returns a list of responses
                responses = response.json()
                if responses and len(responses) > 0:
                    return responses[0]  # Return the first response
            
            return None
            
        except requests.RequestException as e:
            print(f"Error connecting to Rasa server: {e}")
            return None 