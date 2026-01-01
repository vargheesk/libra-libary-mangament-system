import psycopg2
import os
import pickle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def get_all_user_encodings():
    """Returns a list of (id, name, encoding) for all registered users."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, face_encoding FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    # Decode pickle bytes back to numpy arrays
    decoded_users = []
    for uid, name, encoding_bytes in users:
        if encoding_bytes:
            decoded_users.append((uid, name, pickle.loads(encoding_bytes)))
    return decoded_users

def get_user_session_data(user_id):
    """Gets user info and their currently borrowed books."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Get user name
    cur.execute("SELECT name FROM users WHERE id = %s", (user_id,))
    name = cur.fetchone()[0]
    
    # Get active borrowed books
    cur.execute("""
        SELECT bc.barcode, b.title, b.author, t.borrow_date
        FROM transactions t
        JOIN book_copies bc ON t.copy_barcode = bc.barcode
        JOIN books b ON bc.book_isbn = b.isbn
        WHERE t.user_id = %s AND t.return_date IS NULL
    """, (user_id,))
    borrowed_books = cur.fetchall()
    
    cur.close()
    conn.close()
    return {"name": name, "books": borrowed_books}

def process_return(barcode):
    """Marks a book copy as returned."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE transactions 
            SET return_date = CURRENT_TIMESTAMP 
            WHERE copy_barcode = %s AND return_date IS NULL
        """, (barcode,))
        cur.execute("UPDATE book_copies SET status = 'AVAILABLE' WHERE barcode = %s", (barcode,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def process_borrow(user_id, barcode):
    """Registers a new borrow transaction."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if barcode exists and is available
        cur.execute("SELECT status FROM book_copies WHERE barcode = %s", (barcode,))
        res = cur.fetchone()
        if not res or res[0] != 'AVAILABLE':
            return False, "Book is not available or does not exist."
            
        cur.execute("""
            INSERT INTO transactions (user_id, copy_barcode, borrow_date)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
        """, (user_id, barcode))
        
        cur.execute("UPDATE book_copies SET status = 'BORROWED' WHERE barcode = %s", (barcode,))
        
        conn.commit()
        return True, "Successfully borrowed."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()
