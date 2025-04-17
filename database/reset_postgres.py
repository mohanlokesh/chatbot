import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_postgres_db():
    """Drop and recreate the PostgreSQL database"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="postgres",
            port="5432"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Drop database if exists
        print("Dropping existing database...")
        cursor.execute("DROP DATABASE IF EXISTS ai_chatbot")
        
        # Create database
        print("Creating new database...")
        cursor.execute("CREATE DATABASE ai_chatbot")
        
        print("Database reset successfully!")
        
    except Exception as e:
        print(f"Error resetting database: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_postgres_db() 