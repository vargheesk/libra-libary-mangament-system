import psycopg2
import streamlit as st
import pandas as pd
from datetime import datetime

def get_connection():
    return psycopg2.connect(**st.secrets["postgres"])

def add_user(name, face_encoding_bytes):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, face_encoding) VALUES (%s, %s) RETURNING id",
            (name, face_encoding_bytes)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        st.error(f"Error adding user: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, face_encoding FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users

def add_book(isbn, title, author, category, quantity):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Check if book metadata exists
        cur.execute("SELECT isbn FROM books WHERE isbn = %s", (isbn,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO books (isbn, title, author, category) VALUES (%s, %s, %s, %s)",
                (isbn, title, author, category)
            )
        
        # 2. Add copies
        generated_barcodes = []
        for i in range(quantity):
            # Generate unique barcode: ISBN-TIMESTAMP-INDEX (Simple unique logic)
            # Or simpler: ISBN-SEQ
            # Let's use a counter based on existing copies
            cur.execute("SELECT count(*) FROM book_copies WHERE book_isbn = %s", (isbn,))
            count = cur.fetchone()[0]
            new_suffix = count + 1 + i
            barcode = f"{isbn}-{new_suffix:03d}"
            
            cur.execute(
                "INSERT INTO book_copies (barcode, book_isbn) VALUES (%s, %s)",
                (barcode, isbn)
            )
            generated_barcodes.append(barcode)
            
        conn.commit()
        return True, generated_barcodes
    except Exception as e:
        conn.rollback()
        st.error(f"Error adding book: {e}")
        return False, []
    finally:
        cur.close()
        conn.close()

def get_book_copy(barcode):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.barcode, b.title, b.author, c.status 
        FROM book_copies c
        JOIN books b ON c.book_isbn = b.isbn
        WHERE c.barcode = %s
    """, (barcode,))
    book = cur.fetchone()
    cur.close()
    conn.close()
    return book

def borrow_book(user_id, copy_barcode):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if copy is available
        cur.execute("SELECT status FROM book_copies WHERE barcode = %s", (copy_barcode,))
        status = cur.fetchone()
        if not status or status[0] != 'AVAILABLE':
            return False, "Book copy not available"

        # Update copy status
        cur.execute("UPDATE book_copies SET status = 'BORROWED' WHERE barcode = %s", (copy_barcode,))
        
        # Create transaction
        cur.execute(
            "INSERT INTO transactions (user_id, copy_barcode, status) VALUES (%s, %s, 'BORROWED')",
            (user_id, copy_barcode)
        )
        conn.commit()
        return True, "Book borrowed successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def return_book(user_id, copy_barcode):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if borrowed by this user
        cur.execute("""
            SELECT id FROM transactions 
            WHERE user_id = %s AND copy_barcode = %s AND status = 'BORROWED'
        """, (user_id, copy_barcode))
        transaction = cur.fetchone()
        
        if not transaction:
            return False, "No active borrow record found for this book and user"

        # Update copy status
        cur.execute("UPDATE book_copies SET status = 'AVAILABLE' WHERE barcode = %s", (copy_barcode,))
        
        # Update transaction
        cur.execute("""
            UPDATE transactions 
            SET status = 'RETURNED', return_date = %s 
            WHERE id = %s
        """, (datetime.now(), transaction[0]))
        
        conn.commit()
        return True, "Book returned successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def get_user_history(user_id):
    conn = get_connection()
    query = """
        SELECT t.borrow_date, t.return_date, t.status, b.title, b.author, t.copy_barcode
        FROM transactions t
        JOIN book_copies c ON t.copy_barcode = c.barcode
        JOIN books b ON c.book_isbn = b.isbn
        WHERE t.user_id = %s
        ORDER BY t.borrow_date DESC
    """
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df
