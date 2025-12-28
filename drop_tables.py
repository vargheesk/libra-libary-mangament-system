import psycopg2
import toml
import os

def get_db_config():
    secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
    try:
        config = toml.load(secrets_path)
        return config['postgres']
    except Exception as e:
        print(f"Error reading secrets: {e}")
        return None

def drop_tables():
    config = get_db_config()
    if not config: return

    try:
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        
        # Drop in correct order (dependencies first)
        print("Dropping tables...")
        cur.execute("DROP TABLE IF EXISTS transactions CASCADE")
        cur.execute("DROP TABLE IF EXISTS book_copies CASCADE")
        cur.execute("DROP TABLE IF EXISTS books CASCADE")
        cur.execute("DROP TABLE IF EXISTS users CASCADE")
        
        conn.commit()
        cur.close()
        conn.close()
        print("All tables dropped.")
    except Exception as e:
        print(f"Error dropping tables: {e}")

if __name__ == "__main__":
    drop_tables()
