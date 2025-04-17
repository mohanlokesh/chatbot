#!/usr/bin/env python3
"""
Import training data from JSON files into the PostgreSQL database.
This script is used to populate the SupportData table with training examples.
"""

import os
import sys
import json
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path to import database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, SupportData, Company

def import_from_json(file_path, session, company_id=1):
    """
    Import training data from a JSON file into the SupportData table
    
    Args:
        file_path (str): Path to the JSON file
        session: SQLAlchemy session
        company_id (int): Company ID to associate with the data
    
    Returns:
        int: Number of records imported
    """
    try:
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if company exists
        company = session.query(Company).filter_by(id=company_id).first()
        if not company:
            # Create a default company if it doesn't exist
            company = Company(
                id=company_id,
                name="Demo Company",
                description="Demo company for training data",
                contact_email="support@example.com",
                contact_phone="1-800-123-4567",
                website="https://example.com"
            )
            session.add(company)
            session.commit()
            print(f"Created default company with ID {company_id}")
        
        # Count existing records to avoid duplicates
        existing_count = session.query(SupportData).count()
        print(f"Found {existing_count} existing support data records")
        
        # Import data
        import_count = 0
        for item in data:
            # Check if question already exists
            existing = session.query(SupportData).filter_by(
                question=item['question'],
                company_id=company_id
            ).first()
            
            if not existing:
                support_data = SupportData(
                    company_id=company_id,
                    question=item['question'],
                    answer=item['answer'],
                    category=item.get('category', 'General')
                )
                session.add(support_data)
                import_count += 1
        
        # Commit changes
        session.commit()
        print(f"Imported {import_count} new records from {file_path}")
        
        return import_count
    
    except Exception as e:
        session.rollback()
        print(f"Error importing data from {file_path}: {e}")
        return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Import training data from JSON files into PostgreSQL database')
    parser.add_argument('--file', help='Path to JSON file to import', required=False)
    parser.add_argument('--dir', help='Directory containing JSON files to import', required=False)
    parser.add_argument('--company', type=int, default=1, help='Company ID to associate with the data')
    parser.add_argument('--clear', action='store_true', help='Clear existing support data before import')
    
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        parser.error("Either --file or --dir must be specified")
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment variable
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Create database engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Clear existing data if requested
        if args.clear:
            count = session.query(SupportData).delete()
            session.commit()
            print(f"Cleared {count} existing support data records")
        
        # Total import count
        total_import_count = 0
        
        # Import from single file
        if args.file:
            if not os.path.exists(args.file):
                print(f"Error: File {args.file} does not exist")
                sys.exit(1)
            
            total_import_count += import_from_json(args.file, session, args.company)
        
        # Import from directory
        if args.dir:
            if not os.path.exists(args.dir):
                print(f"Error: Directory {args.dir} does not exist")
                sys.exit(1)
            
            for filename in os.listdir(args.dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(args.dir, filename)
                    total_import_count += import_from_json(file_path, session, args.company)
        
        print(f"Import completed. Added {total_import_count} new records.")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        session.close()

if __name__ == "__main__":
    main() 