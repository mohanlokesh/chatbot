import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Get secret key from environment or use default
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

def hash_password(password):
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    """Check if password matches hashed password"""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def generate_token(user_id, username, expires_in=86400):
    """Generate a JWT token"""
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id,
        'username': username
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
    """Decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired. Please log in again.'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token. Please log in again.'}

def token_required(f):
    """Decorator for routes that require a valid token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Flask routes
        from flask import request
        auth_header = request.headers.get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return {'message': 'Token is missing'}, 401
        
        try:
            data = decode_token(token)
            if 'error' in data:
                return {'message': data['error']}, 401
            
            # Add user data to kwargs
            kwargs['user_id'] = data['sub']
            kwargs['username'] = data['username']
            
        except:
            return {'message': 'Token is invalid'}, 401
        
        return f(*args, **kwargs)
    
    return decorated 