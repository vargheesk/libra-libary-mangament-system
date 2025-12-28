import psycopg2
import toml
import os

def get_db_config():
    # Try to read from .streamlit/secrets.toml
    secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
    try:
        config = toml.load(secrets_path)
        return config['postgres']
    except Exception as e:
        print(f"Error reading secrets: {e}")
        return None

def check_db():
    config = get_db_config()
    if not config:
        return

    try:
        conn = psycopg2.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            dbname=config['dbname']
        )
        cur = conn.cursor()
        
        # Check tables
        print("Checking for tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        table_names = [t[0] for t in tables]
        print(f"Tables found: {table_names}")
        
        expected_tables = ['users', 'books', 'transactions']
        missing = [t for t in expected_tables if t not in table_names]
        
        if missing:
            print(f"❌ Missing tables: {missing}")
        else:
            print("✅ All expected tables are present.")

        # Check users
        if 'users' in table_names:
            cur.execute("SELECT count(*) FROM users")
            user_count = cur.fetchone()[0]
            print(f"User count: {user_count}")
            
            if user_count > 0:
                cur.execute("SELECT id, name FROM users LIMIT 5")
                print("Sample users:", cur.fetchall())
        
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    check_db()
