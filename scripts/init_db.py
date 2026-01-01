import psycopg2
from psycopg2 import sql
import toml
import os

def get_db_config():
    # Try to read from .streamlit/secrets.toml
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.streamlit', 'secrets.toml')
    try:
        config = toml.load(secrets_path)
        return config['postgres']
    except Exception as e:
        print(f"Error reading secrets: {e}")
        return None

def create_database(config):
    try:
        # Connect to default 'postgres' db to create the new db
        conn = psycopg2.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            dbname='postgres'
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if db exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (config['dbname'],))
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database {config['dbname']}...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(config['dbname'])
            ))
        else:
            print(f"Database {config['dbname']} already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def create_tables(config):
    try:
        conn = psycopg2.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            dbname=config['dbname']
        )
        cur = conn.cursor()
        
        # Users Table
        print("Creating users table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                face_encoding BYTEA,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Books Table (Metadata)
        print("Creating books table (Metadata)...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                isbn VARCHAR(20) PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(100),
                category VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Book Copies Table (Physical Items)
        print("Creating book_copies table (Physical Items)...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS book_copies (
                barcode VARCHAR(50) PRIMARY KEY,
                book_isbn VARCHAR(20) REFERENCES books(isbn),
                status VARCHAR(20) DEFAULT 'AVAILABLE',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transactions Table
        print("Creating transactions table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                copy_barcode VARCHAR(50) REFERENCES book_copies(barcode),
                borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                return_date TIMESTAMP,
                status VARCHAR(20) DEFAULT 'BORROWED'
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Tables created successfully (Normalized Schema).")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    config = get_db_config()
    if config:
        create_database(config)
        create_tables(config)
