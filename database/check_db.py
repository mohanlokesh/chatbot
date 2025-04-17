import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, User, Conversation, Message, Company, SupportData, Order, OrderItem

# Load environment variables
load_dotenv()

# Get database URL
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    print("No DATABASE_URL found in .env file!")
    sys.exit(1)

print(f"Using database URL: {DB_URL}")

# Create database engine
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Check users
    users = session.query(User).all()
    print(f"\nUsers ({len(users)}):")
    for user in users:
        print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}")

    # Check companies
    companies = session.query(Company).all()
    print(f"\nCompanies ({len(companies)}):")
    for company in companies:
        print(f"  - ID: {company.id}, Name: {company.name}")
        
    # Check support data
    support_data = session.query(SupportData).all()
    print(f"\nSupport Data ({len(support_data)}):")
    for data in support_data:
        print(f"  - ID: {data.id}, Company ID: {data.company_id}")
        print(f"    Q: {data.question}")
        print(f"    A: {data.answer}")
        
    # Check conversations
    conversations = session.query(Conversation).all()
    print(f"\nConversations ({len(conversations)}):")
    for conv in conversations:
        print(f"  - ID: {conv.id}, User ID: {conv.user_id}")
        
    # Check messages
    messages = session.query(Message).all()
    print(f"\nMessages ({len(messages)}):")
    for i, msg in enumerate(messages):
        if i < 5:  # Only show first 5 messages to avoid output overload
            print(f"  - ID: {msg.id}, Conversation ID: {msg.conversation_id}, User: {msg.is_user}")
            print(f"    Content: {msg.content[:50]}...")
    if len(messages) > 5:
        print(f"  ... and {len(messages) - 5} more messages")
        
except Exception as e:
    print(f"Error querying database: {e}")
finally:
    session.close() 