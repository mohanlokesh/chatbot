import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import time
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import hash_password, check_password, generate_token, decode_token, token_required
from database.models import User, Conversation, Message
from models.chatbot import Chatbot

# Load environment variables
load_dotenv()

# Get the absolute project root path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database URL (default to SQLite for development)
# Use absolute path for the SQLite database file
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL or DB_URL.startswith("sqlite:///"):
    DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
    DB_URL = f"sqlite:///{DB_PATH}"
    os.environ["DATABASE_URL"] = DB_URL

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS

# Set higher request timeout
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max request size

# Database setup
engine_args = {}
if "postgresql" in DB_URL:
    engine_args = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
        "connect_args": {"connect_timeout": 30}
    }
    print("Configuring PostgreSQL connection settings for backend")

engine = create_engine(DB_URL, **engine_args)
Session = sessionmaker(bind=engine)

# Initialize chatbot
chatbot = Chatbot(DB_URL)

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    # Get request data
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Validate input
    if not all([username, email, password]):
        return jsonify({"error": "Username, email and password are required"}), 400
    
    # Check if username or email already exists
    session = Session()
    existing_user = session.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        session.close()
        return jsonify({"error": "Username or email already exists"}), 400
    
    # Create new user
    hashed_password = hash_password(password)
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password
    )
    
    session.add(new_user)
    session.commit()
    
    # Generate token
    token = generate_token(new_user.id, new_user.username)
    
    session.close()
    
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Login a user"""
    # Get request data
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Validate input
    if not all([username, password]):
        return jsonify({"error": "Username and password are required"}), 400
    
    # Check if user exists
    session = Session()
    user = session.query(User).filter(User.username == username).first()
    
    if not user or not check_password(password, user.password_hash):
        session.close()
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Update last login
    user.last_login = datetime.now()
    session.commit()
    
    # Generate token
    token = generate_token(user.id, user.username)
    
    session.close()
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200

@app.route('/api/chat', methods=['POST'])
@token_required
def chat(user_id, username):
    """Process a chat message"""
    # Get request data
    data = request.get_json()
    message = data.get('message')
    conversation_id = data.get('conversation_id')
    
    # Validate input
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    # Process message with chatbot
    response = chatbot.process_message(message, user_id, conversation_id)
    
    return jsonify(response), 200

@app.route('/api/conversations', methods=['GET'])
@token_required
def get_conversations(user_id, username):
    """Get all conversations for a user"""
    session = Session()
    
    # Get conversations
    conversations = session.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.start_time.desc()).all()
    
    # Convert to list of dictionaries
    result = []
    for conv in conversations:
        # Get last message
        last_message = session.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.timestamp.desc()).first()
        
        result.append({
            "id": conv.id,
            "start_time": conv.start_time.isoformat(),
            "end_time": conv.end_time.isoformat() if conv.end_time else None,
            "duration": conv.duration,
            "last_message": last_message.content if last_message else None
        })
    
    session.close()
    
    return jsonify(result), 200

@app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
@token_required
def get_conversation(user_id, username, conversation_id):
    """Get a specific conversation"""
    session = Session()
    
    # Check if conversation exists and belongs to user
    conversation = session.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()
    
    if not conversation:
        session.close()
        return jsonify({"error": "Conversation not found"}), 404
    
    # Get messages
    messages = chatbot.get_conversation_history(conversation_id)
    
    session.close()
    
    return jsonify({
        "id": conversation.id,
        "start_time": conversation.start_time.isoformat(),
        "end_time": conversation.end_time.isoformat() if conversation.end_time else None,
        "duration": conversation.duration,
        "messages": messages
    }), 200

@app.route('/api/conversations/<int:conversation_id>', methods=['PUT'])
@token_required
def end_conversation(user_id, username, conversation_id):
    """End a conversation"""
    session = Session()
    
    # Check if conversation exists and belongs to user
    conversation = session.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()
    
    if not conversation:
        session.close()
        return jsonify({"error": "Conversation not found"}), 404
    
    # End conversation
    conversation.end_time = datetime.now()
    
    # Calculate duration
    if conversation.start_time:
        duration = (conversation.end_time - conversation.start_time).total_seconds()
        conversation.duration = duration
    
    session.commit()
    session.close()
    
    return jsonify({
        "message": "Conversation ended",
        "conversation_id": conversation_id
    }), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 