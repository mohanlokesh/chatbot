import streamlit as st
import requests
import json
from datetime import datetime
import os
import sys
import time

# Constants
API_URL = os.getenv("API_URL", "http://localhost:5000/api")

# Session state keys
TOKEN_KEY = "token"
USER_KEY = "user"
CONVERSATION_KEY = "conversation_id"
MESSAGES_KEY = "messages"
LATEST_UPDATE_KEY = "latest_update"

# Page names
LOGIN_PAGE = "Login"
REGISTER_PAGE = "Register"
DASHBOARD_PAGE = "Dashboard"
CHAT_PAGE = "Chat"

def main():
    """Main function for the Streamlit app"""
    # Set page configuration
    st.set_page_config(
        page_title="AI Chatbot",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state variables
    if TOKEN_KEY not in st.session_state:
        st.session_state[TOKEN_KEY] = None
    if USER_KEY not in st.session_state:
        st.session_state[USER_KEY] = None
    if CONVERSATION_KEY not in st.session_state:
        st.session_state[CONVERSATION_KEY] = None
    if MESSAGES_KEY not in st.session_state:
        st.session_state[MESSAGES_KEY] = []
    if LATEST_UPDATE_KEY not in st.session_state:
        st.session_state[LATEST_UPDATE_KEY] = "Welcome to the AI Chatbot"
    
    # Define navigation based on authentication status
    if st.session_state[TOKEN_KEY] is None:
        # User is not logged in
        if 'page' not in st.session_state:
            st.session_state['page'] = LOGIN_PAGE
        
        # Sidebar for navigation
        with st.sidebar:
            st.title("AI Chatbot")
            
            if st.button("Login", key="login_nav"):
                st.session_state['page'] = LOGIN_PAGE
            
            if st.button("Register", key="register_nav"):
                st.session_state['page'] = REGISTER_PAGE
        
        # Display the appropriate page
        if st.session_state['page'] == LOGIN_PAGE:
            login_page()
        elif st.session_state['page'] == REGISTER_PAGE:
            register_page()
    else:
        # User is logged in
        if 'page' not in st.session_state or st.session_state['page'] in [LOGIN_PAGE, REGISTER_PAGE]:
            st.session_state['page'] = DASHBOARD_PAGE
        
        # Sidebar for navigation
        with st.sidebar:
            st.title(f"Welcome, {st.session_state[USER_KEY]['username']}")
            
            if st.button("Dashboard", key="dashboard_nav"):
                st.session_state['page'] = DASHBOARD_PAGE
                # Reset conversation when going back to dashboard
                st.session_state[CONVERSATION_KEY] = None
                st.session_state[MESSAGES_KEY] = []
            
            if st.button("Chat", key="chat_nav"):
                st.session_state['page'] = CHAT_PAGE
                # Start a new conversation if none exists
                if st.session_state[CONVERSATION_KEY] is None:
                    # The conversation will be created when sending the first message
                    pass
            
            if st.button("Logout", key="logout_nav"):
                # Clear session state
                for key in [TOKEN_KEY, USER_KEY, CONVERSATION_KEY, MESSAGES_KEY]:
                    st.session_state[key] = None
                st.session_state['page'] = LOGIN_PAGE
                st.rerun()
        
        # Display the appropriate page
        if st.session_state['page'] == DASHBOARD_PAGE:
            dashboard_page()
        elif st.session_state['page'] == CHAT_PAGE:
            chat_page()

def login_page():
    """Login page"""
    st.title("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not username or not password:
                st.error("Please enter username and password")
            else:
                try:
                    # Call login API
                    response = requests.post(
                        f"{API_URL}/login",
                        json={"username": username, "password": password}
                    )
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            st.session_state[TOKEN_KEY] = data["token"]
                            st.session_state[USER_KEY] = data["user"]
                            st.session_state['page'] = DASHBOARD_PAGE
                            st.success("Login successful")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing response: {e}")
                    else:
                        try:
                            error_msg = response.json().get("error", "Login failed")
                            st.error(error_msg)
                        except:
                            st.error(f"Login failed with status code: {response.status_code}")
                except requests.RequestException as e:
                    st.error(f"Connection error: {e}. Is the backend server running?")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

def register_page():
    """Register page"""
    st.title("Register")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if not username or not email or not password:
                st.error("Please fill all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                try:
                    # Call register API
                    response = requests.post(
                        f"{API_URL}/register",
                        json={"username": username, "email": email, "password": password}
                    )
                    
                    if response.status_code == 201:
                        try:
                            data = response.json()
                            st.session_state[TOKEN_KEY] = data["token"]
                            st.session_state[USER_KEY] = data["user"]
                            st.session_state['page'] = DASHBOARD_PAGE
                            st.success("Registration successful")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing response: {e}")
                    else:
                        try:
                            error_msg = response.json().get("error", "Registration failed")
                            st.error(error_msg)
                        except:
                            st.error(f"Registration failed with status code: {response.status_code}")
                except requests.RequestException as e:
                    st.error(f"Connection error: {e}. Is the backend server running?")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

def dashboard_page():
    """Dashboard page"""
    st.title("Dashboard")
    
    # Latest Update section
    st.subheader("Latest Update")
    st.info(st.session_state[LATEST_UPDATE_KEY])
    
    # Get conversations
    conversations = get_conversations()
    
    if conversations:
        st.subheader("Your Conversations")
        
        for conv in conversations:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{conv['last_message']}**" if conv['last_message'] else "*No messages*")
                
            with col2:
                st.write(f"Started: {format_datetime(conv['start_time'])}")
                
            with col3:
                if st.button("Open", key=f"open_{conv['id']}"):
                    st.session_state[CONVERSATION_KEY] = conv['id']
                    st.session_state['page'] = CHAT_PAGE
                    st.rerun()
        
        # Add button to start new conversation
        if st.button("Start New Conversation"):
            st.session_state[CONVERSATION_KEY] = None
            st.session_state[MESSAGES_KEY] = []
            st.session_state['page'] = CHAT_PAGE
            st.rerun()
    else:
        st.write("No conversations yet.")
        
        # Add button to start new conversation
        if st.button("Start New Conversation"):
            st.session_state[CONVERSATION_KEY] = None
            st.session_state[MESSAGES_KEY] = []
            st.session_state['page'] = CHAT_PAGE
            st.rerun()

def chat_page():
    """Chat page"""
    st.title("Chat with AI")
    
    # Display conversation
    display_messages()
    
    # Message input
    with st.form("message_form", clear_on_submit=True):
        message = st.text_input("Message", key="message_input")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            submitted = st.form_submit_button("Send")
        
        with col2:
            if st.form_submit_button("End Conversation"):
                if st.session_state[CONVERSATION_KEY]:
                    end_conversation(st.session_state[CONVERSATION_KEY])
                st.session_state[CONVERSATION_KEY] = None
                st.session_state[MESSAGES_KEY] = []
                st.session_state['page'] = DASHBOARD_PAGE
                st.rerun()
        
        if submitted and message:
            # Add user message to UI immediately
            st.session_state[MESSAGES_KEY].append({
                "is_user": True,
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send message to API
            response = send_message(message)
            
            if response:
                # Add bot response to UI
                st.session_state[MESSAGES_KEY].append({
                    "is_user": False,
                    "content": response["text"],
                    "timestamp": datetime.now().isoformat()
                })
                
                # Set conversation ID if new
                if not st.session_state[CONVERSATION_KEY]:
                    st.session_state[CONVERSATION_KEY] = response["conversation_id"]
                
                # Set latest update
                st.session_state[LATEST_UPDATE_KEY] = f"Last chat: {format_datetime(datetime.now().isoformat())}"
                
                # Rerun to update UI
                st.rerun()

def display_messages():
    """Display messages in the chat"""
    # Get conversation history if needed
    if st.session_state[CONVERSATION_KEY] and not st.session_state[MESSAGES_KEY]:
        fetch_conversation(st.session_state[CONVERSATION_KEY])
    
    # Create a container for messages
    message_container = st.container()
    
    with message_container:
        for msg in st.session_state[MESSAGES_KEY]:
            col1, col2 = st.columns([1, 7])
            
            with col1:
                if msg["is_user"]:
                    st.write("You:")
                else:
                    st.write("Bot:")
            
            with col2:
                if msg["is_user"]:
                    st.text_area("", msg["content"], height=50, key=f"msg_{msg['timestamp']}", disabled=True, 
                                label_visibility="collapsed")
                else:
                    st.info(msg["content"])

def send_message(message):
    """Send a message to the API"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state[TOKEN_KEY]}"}
        data = {
            "message": message
        }
        
        if st.session_state[CONVERSATION_KEY]:
            data["conversation_id"] = st.session_state[CONVERSATION_KEY]
        
        response = requests.post(
            f"{API_URL}/chat",
            json=data,
            headers=headers,
            timeout=120  # Increased timeout
        )
        
        if response.status_code == 200:
            try:
                return response.json()
            except Exception as e:
                st.error(f"Error parsing response: {e}")
                return None
        else:
            try:
                error_msg = response.json().get("error", "Failed to send message")
                st.error(f"Error: {error_msg}")
            except:
                st.error(f"Failed to send message. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Connection error: {e}. Is the backend server running?")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def get_conversations():
    """Get conversations from the API"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state[TOKEN_KEY]}"}
        response = requests.get(
            f"{API_URL}/conversations",
            headers=headers,
            timeout=30  # Increased timeout
        )
        
        if response.status_code == 200:
            try:
                return response.json()
            except Exception as e:
                st.error(f"Error parsing response: {e}")
                return []
        else:
            try:
                error_msg = response.json().get("error", "Failed to get conversations")
                st.error(f"Error: {error_msg}")
            except:
                st.error(f"Failed to get conversations. Status code: {response.status_code}")
            return []
    except requests.RequestException as e:
        st.error(f"Connection error: {e}. Is the backend server running?")
        return []
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return []

def fetch_conversation(conversation_id):
    """Fetch conversation history from the API"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state[TOKEN_KEY]}"}
        response = requests.get(
            f"{API_URL}/conversations/{conversation_id}",
            headers=headers,
            timeout=30  # Increased timeout
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                st.session_state[MESSAGES_KEY] = data["messages"]
                return data
            except Exception as e:
                st.error(f"Error parsing response: {e}")
                return None
        else:
            try:
                error_msg = response.json().get("error", "Failed to fetch conversation")
                st.error(f"Error: {error_msg}")
            except:
                st.error(f"Failed to fetch conversation. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Connection error: {e}. Is the backend server running?")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def end_conversation(conversation_id):
    """End a conversation"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state[TOKEN_KEY]}"}
        response = requests.put(
            f"{API_URL}/conversations/{conversation_id}",
            headers=headers,
            timeout=30  # Increased timeout
        )
        
        if response.status_code == 200:
            return True
        else:
            try:
                error_msg = response.json().get("error", "Failed to end conversation")
                st.error(f"Error: {error_msg}")
            except:
                st.error(f"Failed to end conversation. Status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        st.error(f"Connection error: {e}. Is the backend server running?")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return False

def format_datetime(dt_string):
    """Format datetime string for display"""
    if "T" in dt_string:
        dt = datetime.fromisoformat(dt_string)
    else:
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M")

if __name__ == "__main__":
    main() 