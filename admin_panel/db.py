import psycopg2
import toml
import os
from datetime import datetime
import pandas as pd

def get_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    secrets_path = os.path.join(base_dir, '.streamlit', 'secrets.toml')
    return toml.load(secrets_path)

def get_connection():
    config = get_config()
    return psycopg2.connect(**config['postgres'])

# --- USER CRUD ---

def add_user(name, face_encoding_bytes, dob=None, phone=None, address=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, face_encoding, dob, phone, address) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (name, face_encoding_bytes, dob, phone, address)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at, phone FROM users ORDER BY created_at DESC")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users

def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, dob, phone, address FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def update_user(user_id, name, dob=None, phone=None, address=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET name = %s, dob = %s, phone = %s, address = %s WHERE id = %s",
            (name, dob, phone, address, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Transactions will be handled by ON DELETE CASCADE if set up, 
        # but let's be safe or just check if user has active borrows
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# --- BOOK CRUD ---

def get_all_books():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.isbn, b.title, b.author, b.category, 
               COUNT(c.barcode) as total_copies,
               COUNT(CASE WHEN c.status = 'AVAILABLE' THEN 1 END) as available_copies
        FROM books b
        LEFT JOIN book_copies c ON b.isbn = c.book_isbn
        GROUP BY b.isbn
        ORDER BY b.title
    """)
    books = cur.fetchall()
    cur.close()
    conn.close()
    return books

def get_book(isbn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT isbn, title, author, category FROM books WHERE isbn = %s", (isbn,))
    book = cur.fetchone()
    cur.close()
    conn.close()
    return book

def add_book_bulk(isbn, title, author, category, quantity):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if book metadata exists
        cur.execute("SELECT isbn FROM books WHERE isbn = %s", (isbn,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO books (isbn, title, author, category) VALUES (%s, %s, %s, %s)",
                (isbn, title, author, category)
            )
        
        generated_barcodes = []
        for i in range(quantity):
            cur.execute("SELECT count(*) FROM book_copies WHERE book_isbn = %s", (isbn,))
            count = cur.fetchone()[0]
            barcode = f"{isbn}-{count + 1 + i:03d}"
            cur.execute(
                "INSERT INTO book_copies (barcode, book_isbn) VALUES (%s, %s)",
                (barcode, isbn)
            )
            generated_barcodes.append(barcode)
            
        conn.commit()
        return True, generated_barcodes
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def update_book(isbn, title, author, category):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE books SET title = %s, author = %s, category = %s WHERE isbn = %s",
            (title, author, category, isbn)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def delete_book(isbn):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Note: In a real system, you might want to check for active borrows
        cur.execute("DELETE FROM books WHERE isbn = %s", (isbn,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_book_copies(isbn):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT barcode, status FROM book_copies WHERE book_isbn = %s", (isbn,))
    copies = cur.fetchall()
    cur.close()
    conn.close()
    return copies

def delete_copy(barcode):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM book_copies WHERE barcode = %s", (barcode,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# --- DASHBOARD STATS ---

def get_stats():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM books")
    total_books = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM book_copies WHERE status = 'BORROWED'")
    total_borrowed = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM book_copies")
    total_copies = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return {
        'total_books': total_books,
        'total_users': total_users,
        'total_borrowed': total_borrowed,
        'total_copies': total_copies
    }
