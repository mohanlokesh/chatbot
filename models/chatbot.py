import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.nlp_utils import preprocess_text, extract_entities, find_best_matches, calculate_keyword_overlap
from utils.transformer_utils import semantic_faqs_search, find_semantic_matches
from database.models import SupportData, Message, Conversation

# Import Rasa integration if available
try:
    from utils.rasa_integration import RasaIntegration
    RASA_AVAILABLE = True
except ImportError:
    RASA_AVAILABLE = False

class Chatbot:
    """Chatbot implementation with transformer-based semantic search and Rasa NLP capabilities"""
    
    def __init__(self, db_url=None, use_rasa=True):
        """Initialize chatbot with database connection"""
        if not db_url:
            # Get the absolute project root path
            PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Use absolute path for the SQLite database file
            db_url = os.getenv("DATABASE_URL")
            if not db_url or db_url.startswith("sqlite:///"):
                DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
                db_url = f"sqlite:///{DB_PATH}"
        
        self.db_url = db_url
        
        # Configure PostgreSQL settings if using PostgreSQL
        engine_args = {}
        if "postgresql" in db_url:
            engine_args = {
                "pool_pre_ping": True,
                "pool_recycle": 300,
                "pool_size": 10,
                "max_overflow": 20,
                "connect_args": {"connect_timeout": 30}
            }
            print("Configuring PostgreSQL connection settings for chatbot")
        
        self.engine = create_engine(self.db_url, **engine_args)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize with empty cache for support data
        self.support_data_cache = None
        
        # Greeting templates
        self.greetings = [
            "Hello! How can I help you today?",
            "Hi there! What can I assist you with?",
            "Welcome! How may I help you?",
            "Greetings! What do you need help with today?"
        ]
        
        # Fallback templates
        self.fallbacks = [
            "I'm sorry, I don't have information about that topic. I can help with questions about orders, shipping, returns, and using our website.",
            "I don't have enough information to answer that. I specialize in customer support for our online store. Is there something about your order I can help with?",
            "That's outside my area of expertise. I can assist with orders, returns, shipping, and account questions. How can I help you with one of those?",
            "I'm not able to provide information on that topic. Would you like help with something related to our store, like placing an order or tracking a package?"
        ]
        
        # Similarity thresholds
        self.transformer_threshold = 0.6  # Increased from 0.4 to be more precise
        self.similarity_threshold = 0.35  # Increased from 0.25 for more precision
        self.keyword_threshold = 0.6      # Increased from 0.5 for more precision
        self.out_of_domain_threshold = 0.3  # New threshold for out-of-domain detection
        
        # Known domains we can handle
        self.known_domains = [
            "order", "shipping", "return", "refund", "account", "payment",
            "promo code", "discount", "delivery", "track", "website", "login",
            "password", "checkout", "product", "price", "store"
        ]
        
        # Initialize Rasa integration if available and requested
        self.use_rasa = use_rasa and RASA_AVAILABLE
        self.rasa_integration = None
        
        if self.use_rasa:
            try:
                self.rasa_integration = RasaIntegration(db_url=db_url)
                print("Initialized with Rasa NLP capability")
            except Exception as e:
                print(f"Failed to initialize Rasa integration: {e}")
                self.use_rasa = False
        
        if self.use_rasa:
            print("Chatbot initialized with Rasa NLP capability")
        else:
            print("Chatbot initialized with transformer-based semantic search capability")
    
    def load_support_data(self, use_cache=True):
        """Load support data from database"""
        # Return cached data if available and requested
        if use_cache and self.support_data_cache is not None:
            return self.support_data_cache
            
        session = self.Session()
        try:
            # Get all support data from database
            support_data = session.query(SupportData).all()
            
            # Convert to list of dictionaries
            data = []
            for item in support_data:
                data.append({
                    'question': item.question,
                    'answer': item.answer,
                    'category': item.category,
                    'company_id': item.company_id
                })
            
            # Cache the data
            self.support_data_cache = data
            
            return data
        finally:
            session.close()
    
    def get_greeting(self):
        """Return a random greeting"""
        return random.choice(self.greetings)
    
    def get_fallback(self):
        """Return a random fallback response"""
        return random.choice(self.fallbacks)
    
    def is_out_of_domain(self, query):
        """Check if a query is outside our domain of expertise"""
        # Check if query is semantically related to any of our known domains
        matches = find_semantic_matches(query, self.known_domains, threshold=self.out_of_domain_threshold)
        
        # If no matches to our domains, it's out of domain
        return len(matches) == 0
    
    def process_message(self, message_text, user_id, conversation_id=None):
        """
        Process a user message and generate a response
        
        Args:
            message_text (str): The user's message
            user_id (int): The user's ID
            conversation_id (int, optional): The conversation ID
            
        Returns:
            dict: Response with text and metadata
        """
        # If Rasa is available and enabled, use it for processing
        if self.use_rasa and self.rasa_integration:
            try:
                # Use Rasa for NLP processing
                return self.rasa_integration.process_message(message_text, user_id, conversation_id)
            except Exception as e:
                print(f"Error using Rasa for processing: {e}")
                print("Falling back to transformer-based processing")
                # Fall back to our own processing if Rasa fails
        
        # Otherwise use our built-in transformer-based processing
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
            
            # Check for greeting patterns
            greeting_patterns = ['hello', 'hi', 'hey', 'greetings', 'howdy', 'welcome']
            if any(pattern in message_text.lower() for pattern in greeting_patterns) and len(message_text.split()) < 4:
                response_text = self.get_greeting()
            # Check if query is out of domain
            elif self.is_out_of_domain(message_text):
                response_text = self.get_fallback()
            else:
                # Try to find answer in support data
                response_text = self.find_answer(message_text)
            
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
    
    def find_answer(self, query):
        """Find the best answer for a query using multiple matching strategies"""
        # Load support data
        support_data = self.load_support_data()
        
        if not support_data:
            return self.get_fallback()
        
        # First check if query is out of domain
        if self.is_out_of_domain(query):
            return self.get_fallback()
        
        # First try transformer-based semantic search (most accurate)
        semantic_match = semantic_faqs_search(query, support_data, threshold=self.transformer_threshold)
        if semantic_match:
            return semantic_match['answer']
        
        # If no semantic match, fall back to traditional methods
        
        # Extract questions and answers
        questions = [item['question'] for item in support_data]
        answers = [item['answer'] for item in support_data]
        
        # Find best matches using TF-IDF
        matches = find_best_matches(query, questions, top_n=5)
        
        # Return best match if score is above threshold
        if matches and matches[0][1] > self.similarity_threshold:
            best_match_index = questions.index(matches[0][0])
            return answers[best_match_index]
        
        # If no good TF-IDF matches, try keyword overlap
        for i, question in enumerate(questions):
            overlap_score = calculate_keyword_overlap(query, question)
            if overlap_score > self.keyword_threshold:
                return answers[i]
        
        # No good matches found, return fallback
        return self.get_fallback()
    
    def get_conversation_history(self, conversation_id, limit=10):
        """Get conversation history"""
        session = self.Session()
        try:
            # Get messages
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp).all()
            
            # Convert to list of dictionaries
            result = []
            for msg in messages:
                result.append({
                    "id": msg.id,
                    "is_user": msg.is_user,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                })
            
            return result
        finally:
            session.close()

class TransformerChatbot:
    """Advanced chatbot implementation using transformer-based models for semantic understanding"""
    
    def __init__(self, faqs=None, db_url=None):
        """
        Initialize the transformer-based chatbot
        
        Args:
            faqs (list, optional): List of FAQ dictionaries with 'question' and 'answer' keys
            db_url (str, optional): Database URL for loading FAQs if not provided directly
        """
        # Initialize database connection if provided
        self.db_url = db_url
        if db_url:
            self.engine = create_engine(self.db_url)
            self.Session = sessionmaker(bind=self.engine)
        
        # Store FAQs if provided directly
        self.faqs = faqs
        
        # Similarity thresholds
        self.semantic_threshold = 0.65  # High threshold for semantic matching
        
        # Greeting and fallback responses
        self.greetings = [
            "Hello! I'm your AI assistant. How can I help you today?",
            "Hi there! I'm ready to answer your questions. What can I help you with?",
            "Welcome! I'm here to assist you. What would you like to know?",
            "Greetings! I'm your virtual assistant. How may I help you today?"
        ]
        
        self.fallbacks = [
            "I'm sorry, but I don't have enough information to answer that question accurately.",
            "I don't have a specific answer for that. Could you try rephrasing your question?",
            "That's beyond my current knowledge. Is there something else I can help with?",
            "I'm not able to provide information on that topic yet. Can I help with something else?"
        ]
        
        print("TransformerChatbot initialized with advanced semantic understanding capabilities")
    
    def load_faqs(self):
        """Load FAQs from database if not provided during initialization"""
        if self.faqs is not None:
            return self.faqs
            
        if not hasattr(self, 'Session'):
            raise ValueError("Database URL was not provided, cannot load FAQs from database")
            
        session = self.Session()
        try:
            # Get all support data from database
            support_data = session.query(SupportData).all()
            
            # Convert to list of dictionaries
            faqs = []
            for item in support_data:
                faqs.append({
                    'question': item.question,
                    'answer': item.answer,
                    'category': item.category,
                    'company_id': item.company_id
                })
            
            # Cache the faqs
            self.faqs = faqs
            
            return faqs
        finally:
            session.close()
    
    def get_greeting(self):
        """Return a random greeting"""
        return random.choice(self.greetings)
    
    def get_fallback(self):
        """Return a random fallback response"""
        return random.choice(self.fallbacks)
    
    def find_answer(self, query):
        """
        Find the best answer for a query using transformer-based semantic search
        
        Args:
            query (str): The user's question
            
        Returns:
            str: The best matching answer or a fallback response
        """
        # Load FAQs if not already loaded
        faqs = self.load_faqs()
        
        if not faqs:
            return self.get_fallback()
        
        # Use transformer-based semantic search
        semantic_match = semantic_faqs_search(query, faqs, threshold=self.semantic_threshold)
        
        if semantic_match:
            return semantic_match['answer']
        
        # Return fallback if no good match
        return self.get_fallback()
    
    def process_question(self, question):
        """
        Process a user question and return the best matching answer
        
        Args:
            question (str): The user's question
            
        Returns:
            str: The best matching answer or a fallback response
        """
        # Check for greeting patterns
        greeting_patterns = ['hello', 'hi', 'hey', 'greetings', 'howdy', 'welcome']
        if any(pattern in question.lower() for pattern in greeting_patterns) and len(question.split()) < 4:
            return self.get_greeting()
        
        # Find the best answer
        return self.find_answer(question) 