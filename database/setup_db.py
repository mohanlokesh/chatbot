import os
import sys
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import argparse

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, User, Conversation, Message, Company, SupportData

# Load environment variables
load_dotenv()

# Get the absolute project root path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database URL (default to SQLite for development)
# Use absolute path for the SQLite database file
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
    DB_URL = f"sqlite:///{DB_PATH}"
    os.environ["DATABASE_URL"] = DB_URL
    print(f"No DATABASE_URL found in .env, defaulting to SQLite: {DB_URL}")
else:
    print(f"Using database URL from .env: {DB_URL}")

def check_existing_data(session):
    """Check and print counts of existing data in the database"""
    user_count = session.query(User).count()
    company_count = session.query(Company).count()
    support_data_count = session.query(SupportData).count()
    conversation_count = session.query(Conversation).count()
    message_count = session.query(Message).count()
    
    print("\nExisting data in database:")
    print(f"- Users: {user_count}")
    print(f"- Companies: {company_count}")
    print(f"- Support Data: {support_data_count}")
    print(f"- Conversations: {conversation_count}")
    print(f"- Messages: {message_count}")
    
    return user_count > 0

def setup_database(force_add_sample_data=False):
    """Create database and tables"""
    print("Setting up database...")
    
    try:
        # Create SQLite file directory if not exists
        if DB_URL.startswith("sqlite:///"):
            db_path = DB_URL.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        # Configure PostgreSQL settings if using PostgreSQL
        engine_args = {}
        if "postgresql" in DB_URL:
            engine_args = {
                "pool_pre_ping": True,
                "pool_recycle": 300,
                "pool_size": 5,
                "max_overflow": 10
            }
            print("Configuring PostgreSQL connection settings")
        
        # Create database engine
        engine = create_engine(DB_URL, **engine_args)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if tables are created
        print("Tables created:")
        for table in Base.metadata.tables:
            print(f"- {table}")
        
        # Check if data exists and add sample data if needed
        has_data = check_existing_data(session)
        if not has_data or force_add_sample_data:
            add_sample_data(session)
        else:
            print("\nDatabase already contains data. Skipping sample data creation.")
            print("Run with --force-add-sample-data to add sample data anyway.")
        
        session.close()
        print("Database setup complete!")
    except Exception as e:
        print(f"Error setting up database: {e}")
        if "postgresql" in DB_URL:
            print("\nPostgreSQL connection failed. Please check:")
            print("1. Your DATABASE_URL in .env is correct")
            print("2. PostgreSQL server is running and accessible")
            print("3. Network/firewall settings allow the connection")
            print("4. Database exists and user has proper permissions")
            print(f"\nCurrent DATABASE_URL: {DB_URL}")
        sys.exit(1)

def add_sample_data(session):
    """Add sample data to the database"""
    print("Adding sample data...")
    
    # Add sample user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        # In production, we would use a proper password hashing library
        password_hash="$2b$12$FiNlQ5pQd8iRfJVbVLjGIeWTvVMSGJ7xK4tC8x/h.S4XtH/HkQkuu"  # "password123"
    )
    session.add(admin_user)
    
    # Add sample company
    company = Company(
        name="Example Corp",
        description="A sample company for demonstration",
        contact_email="contact@example.com",
        contact_phone="555-123-4567",
        website="https://example.com"
    )
    session.add(company)
    
    # Add sample support data
    support_data = [
        SupportData(
            company=company,
            question="How do I reset my password?",
            answer="You can reset your password by clicking on the 'Forgot Password' link on the login page.",
            category="Account"
        ),
        SupportData(
            company=company,
            question="What payment methods do you accept?",
            answer="We accept Visa, Mastercard, American Express, and PayPal.",
            category="Payments"
        ),
        SupportData(
            company=company,
            question="How do I contact customer support?",
            answer="You can contact our customer support team at support@example.com or call us at 555-123-4567.",
            category="Support"
        )
    ]
    session.add_all(support_data)
    
    # Commit changes
    session.commit()
    print("Sample data added!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Setup database for AI chatbot.')
    parser.add_argument('--force-add-sample-data', action='store_true', 
                        help='Add sample data even if data already exists')
    args = parser.parse_args()
    
    setup_database(force_add_sample_data=args.force_add_sample_data) 