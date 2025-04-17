import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, User, Conversation, Message, Company, SupportData, Order, OrderItem

def reset_sequences(engine):
    """Reset sequences for all tables"""
    tables = ['users', 'companies', 'conversations', 'messages', 'support_data', 'orders', 'order_items']
    with engine.connect() as conn:
        for table in tables:
            conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1, false);"))

def migrate_to_postgres():
    """Migrate data from SQLite to PostgreSQL"""
    load_dotenv()
    
    # Get the absolute project root path
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Get database URLs
    sqlite_path = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
    sqlite_url = f"sqlite:///{sqlite_path}"
    postgres_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_chatbot")
    
    print(f"SQLite database path: {sqlite_path}")
    print(f"PostgreSQL URL: {postgres_url}")
    
    # Create engines
    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_engine(postgres_url)
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()
    
    try:
        # Drop all tables in PostgreSQL
        print("Dropping existing tables...")
        Base.metadata.drop_all(postgres_engine)
        
        # Create tables in PostgreSQL
        print("Creating tables...")
        Base.metadata.create_all(postgres_engine)
        
        # Reset sequences
        print("Resetting sequences...")
        reset_sequences(postgres_engine)
        
        # Migrate Users
        print("Migrating users...")
        users = sqlite_session.query(User).all()
        for user in users:
            postgres_session.add(User(
                username=user.username,
                email=user.email,
                password_hash=user.password_hash,
                created_at=user.created_at,
                last_login=user.last_login,
                is_active=user.is_active
            ))
        postgres_session.commit()
        
        # Migrate Companies
        print("Migrating companies...")
        companies = sqlite_session.query(Company).all()
        for company in companies:
            postgres_session.add(Company(
                name=company.name,
                description=company.description,
                contact_email=company.contact_email,
                contact_phone=company.contact_phone,
                website=company.website
            ))
        postgres_session.commit()
        
        # Migrate SupportData
        print("Migrating support data...")
        support_data = sqlite_session.query(SupportData).all()
        for data in support_data:
            postgres_session.add(SupportData(
                company_id=data.company_id,
                question=data.question,
                answer=data.answer,
                category=data.category,
                created_at=data.created_at,
                updated_at=data.updated_at
            ))
        postgres_session.commit()
        
        # Migrate Conversations
        print("Migrating conversations...")
        conversations = sqlite_session.query(Conversation).all()
        for conv in conversations:
            postgres_session.add(Conversation(
                user_id=conv.user_id,
                start_time=conv.start_time,
                end_time=conv.end_time,
                duration=conv.duration
            ))
        postgres_session.commit()
        
        # Migrate Messages
        print("Migrating messages...")
        messages = sqlite_session.query(Message).all()
        for msg in messages:
            postgres_session.add(Message(
                conversation_id=msg.conversation_id,
                is_user=msg.is_user,
                content=msg.content,
                timestamp=msg.timestamp
            ))
        postgres_session.commit()
        
        # Migrate Orders
        print("Migrating orders...")
        orders = sqlite_session.query(Order).all()
        for order in orders:
            postgres_session.add(Order(
                order_number=order.order_number,
                user_id=order.user_id,
                total_amount=order.total_amount,
                status=order.status,
                ordered_at=order.ordered_at,
                estimated_delivery=order.estimated_delivery,
                delivered_at=order.delivered_at,
                shipping_address=order.shipping_address,
                tracking_number=order.tracking_number
            ))
        postgres_session.commit()
        
        # Migrate OrderItems
        print("Migrating order items...")
        order_items = sqlite_session.query(OrderItem).all()
        for item in order_items:
            postgres_session.add(OrderItem(
                order_id=item.order_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price
            ))
        postgres_session.commit()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        postgres_session.rollback()
        raise
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == "__main__":
    migrate_to_postgres() 