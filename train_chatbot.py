"""
Script to train the chatbot with data from various sources
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrape_ecommerce_data import scrape_and_save
from utils.scraper import scrape_website, scrape_multiple_urls
from database.models import Base, Company, SupportData

def setup_database_connection():
    """Set up database connection"""
    load_dotenv()
    
    # Get the absolute project root path
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    
    # Database URL (default to SQLite for development)
    DB_URL = os.getenv("DATABASE_URL")
    if not DB_URL or DB_URL.startswith("sqlite:///"):
        DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
        DB_URL = f"sqlite:///{DB_PATH}"
    
    # Create database engine
    engine = create_engine(DB_URL)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return session, engine

def add_custom_data_to_database(session, company_name, data_list):
    """Add custom data to database for a specific company"""
    # Check if company exists, or create it
    company = session.query(Company).filter(Company.name == company_name).first()
    
    if not company:
        company = Company(
            name=company_name,
            description=f"Custom data for {company_name}",
            contact_email=f"contact@{company_name.lower().replace(' ', '')}.com",
            website=f"https://www.{company_name.lower().replace(' ', '')}.com"
        )
        session.add(company)
        session.commit()
    
    # Add data to database
    count = 0
    for item in data_list:
        # Check if this question already exists to avoid duplicates
        existing = session.query(SupportData).filter(
            SupportData.question == item['question']
        ).first()
        
        if not existing:
            support_data = SupportData(
                company=company,
                question=item['question'],
                answer=item['answer'],
                category=item.get('category', 'General')
            )
            session.add(support_data)
            count += 1
    
    # Commit changes
    session.commit()
    return count

def scrape_custom_website(url, company_name):
    """Scrape a custom website and add the data to the database"""
    print(f"Scraping {url} for {company_name}...")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scraped")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace('.', '_')
    path = urlparse(url).path.replace('/', '_').replace('.', '_')
    output_file = os.path.join(output_dir, f"{domain}{path}.json")
    
    # Scrape website
    scraped_data = scrape_website(url, output_file)
    
    # Add to database
    session, engine = setup_database_connection()
    
    try:
        items_added = add_custom_data_to_database(session, company_name, scraped_data)
        print(f"Added {items_added} new items to database for {company_name}")
    finally:
        session.close()
    
    return len(scraped_data)

def show_database_stats():
    """Show statistics about the training data in the database"""
    session, engine = setup_database_connection()
    
    try:
        # Count companies
        company_count = session.query(Company).count()
        
        # Count support data
        support_data_count = session.query(SupportData).count()
        
        # Count by company
        companies = session.query(Company).all()
        company_stats = []
        
        for company in companies:
            data_count = session.query(SupportData).filter(
                SupportData.company_id == company.id
            ).count()
            
            company_stats.append({
                'name': company.name,
                'count': data_count
            })
        
        # Print stats
        print("\n===== Chatbot Training Data Statistics =====")
        print(f"Total companies: {company_count}")
        print(f"Total support data items: {support_data_count}")
        print("\nData by company:")
        
        for stat in company_stats:
            print(f"- {stat['name']}: {stat['count']} items")
        
        print("===========================================\n")
        
    finally:
        session.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Train the chatbot with data from various sources")
    
    # Add arguments
    parser.add_argument('--ecommerce', action='store_true', help='Scrape e-commerce FAQ data')
    parser.add_argument('--url', type=str, help='Scrape a specific URL')
    parser.add_argument('--company', type=str, help='Company name for the URL data')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show stats if requested
    if args.stats:
        show_database_stats()
        return
    
    # Scrape e-commerce data if requested
    if args.ecommerce:
        scrape_and_save()
    
    # Scrape custom URL if provided
    if args.url:
        company_name = args.company or "Custom Company"
        scrape_custom_website(args.url, company_name)
    
    # If no options provided, show help
    if not args.ecommerce and not args.url and not args.stats:
        parser.print_help()
        
        # Also show stats
        show_database_stats()

if __name__ == "__main__":
    main() 