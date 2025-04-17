import os
import sys
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
import argparse

# Add parent directory to path to access our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, Order, OrderItem, OrderStatus, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

def create_order_tables():
    """Create orders tables in the database"""
    # Get project root path
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Database URL
    DB_URL = os.getenv("DATABASE_URL")
    if not DB_URL:
        DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
        DB_URL = f"sqlite:///{DB_PATH}"
        print(f"No DATABASE_URL found in .env, defaulting to SQLite: {DB_URL}")
    else:
        print(f"Using database URL from .env: {DB_URL}")
    
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
        
        # Create engine and tables
        engine = create_engine(DB_URL, **engine_args)
        
        # Create the tables if they don't exist
        Base.metadata.create_all(engine, tables=[Order.__table__, OrderItem.__table__])
        
        print("Order tables created successfully.")
        return engine
    except Exception as e:
        print(f"Error creating order tables: {e}")
        if "postgresql" in DB_URL:
            print("\nPostgreSQL connection failed. Please check:")
            print("1. Your DATABASE_URL in .env is correct")
            print("2. PostgreSQL server is running and accessible")
            print("3. Network/firewall settings allow the connection")
            print("4. Database exists and user has proper permissions")
            print(f"\nCurrent DATABASE_URL: {DB_URL}")
        sys.exit(1)

def seed_sample_orders(engine, num_orders=20):
    """Seed the database with sample orders"""
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    orders_created = 0
    
    try:
        # Check if users exist
        users = session.query(User).all()
        if not users:
            print("No users found in the database. Please run setup_db.py first to create users.")
            return
            
        print(f"Found {len(users)} users in the database.")
        print(f"Attempting to create {num_orders} sample orders...")
        
        # Sample products with price ranges
        products = [
            {"name": "Smartphone X", "price_range": (499.99, 1299.99)},
            {"name": "Laptop Pro", "price_range": (899.99, 2499.99)},
            {"name": "Wireless Headphones", "price_range": (79.99, 349.99)},
            {"name": "Smart Watch", "price_range": (199.99, 499.99)},
            {"name": "Tablet Ultra", "price_range": (329.99, 999.99)},
            {"name": "Gaming Console", "price_range": (299.99, 599.99)},
            {"name": "Digital Camera", "price_range": (249.99, 1499.99)},
            {"name": "Bluetooth Speaker", "price_range": (59.99, 299.99)},
            {"name": "Fitness Tracker", "price_range": (49.99, 149.99)},
            {"name": "4K Monitor", "price_range": (199.99, 799.99)}
        ]
        
        # Generate orders
        for i in range(1, num_orders + 1):
            # Generate a random order number
            order_number = f"ORD-{random.randint(10000, 99999)}"
            
            # Select a random user
            user = random.choice(users)
            
            # Determine order date (between 1-60 days ago)
            days_ago = random.randint(1, 60)
            order_date = datetime.now() - timedelta(days=days_ago)
            
            # Determine number of items in the order (1-5)
            num_items = random.randint(1, 5)
            
            # Select products for the order
            order_products = random.sample(products, num_items)
            
            # Calculate total amount
            total_amount = 0
            
            # Choose a random status biased towards being complete
            status_choices = [
                OrderStatus.PENDING,
                OrderStatus.PROCESSING,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED,
                OrderStatus.CANCELLED,
                OrderStatus.BACKORDERED
            ]
            status_weights = [0.1, 0.2, 0.2, 0.3, 0.1, 0.1]  # More likely to be delivered
            order_status = random.choices(status_choices, weights=status_weights)[0]
            
            # Calculate estimated and actual delivery dates
            estimated_delivery = order_date + timedelta(days=random.randint(3, 14))
            delivered_at = None
            if order_status == OrderStatus.DELIVERED:
                # Delivered between order date and estimated delivery
                delivered_at = order_date + timedelta(days=random.randint(2, min(13, (estimated_delivery - order_date).days)))
            
            # Create the order
            order = Order(
                order_number=order_number,
                user_id=user.id,
                total_amount=0,  # Will update after adding items
                status=order_status,
                ordered_at=order_date,
                estimated_delivery=estimated_delivery,
                delivered_at=delivered_at,
                shipping_address=f"{random.randint(1, 999)} Main St, City, State, {random.randint(10000, 99999)}",
                tracking_number=f"TRK-{random.randint(1000000, 9999999)}" if order_status not in [OrderStatus.PENDING, OrderStatus.PROCESSING] else None
            )
            
            session.add(order)
            session.flush()  # Flush to get the order ID
            
            # Add order items
            for product in order_products:
                # Random price within the product's range
                min_price, max_price = product["price_range"]
                price = round(random.uniform(min_price, max_price), 2)
                
                # Random quantity (1-3)
                quantity = random.randint(1, 3)
                
                # Create order item
                order_item = OrderItem(
                    order_id=order.id,
                    product_name=product["name"],
                    quantity=quantity,
                    price=price
                )
                
                session.add(order_item)
                
                # Add to total
                total_amount += price * quantity
            
            # Update order total
            order.total_amount = round(total_amount, 2)
        
        # Commit changes
        session.commit()
        
        print(f"Successfully created {num_orders} sample orders.")
        
    except Exception as e:
        print(f"Error seeding orders: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create order tables and seed with sample data.')
    parser.add_argument('--orders', type=int, default=20, help='Number of sample orders to create')
    args = parser.parse_args()
    
    print(f"Starting order migration with {args.orders} sample orders...")
    engine = create_order_tables()
    seed_sample_orders(engine, num_orders=args.orders)
    print("Order migration completed successfully.") 