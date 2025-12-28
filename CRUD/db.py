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

def add_book(barcode, title, author):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO books (barcode, title, author) VALUES (%s, %s, %s)",
            (barcode, title, author)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error adding book: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_book(barcode):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT barcode, title, author, status FROM books WHERE barcode = %s", (barcode,))
    book = cur.fetchone()
    cur.close()
    conn.close()
    return book

def borrow_book(user_id, book_barcode):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if book is available
        cur.execute("SELECT status FROM books WHERE barcode = %s", (book_barcode,))
        status = cur.fetchone()
        if not status or status[0] != 'AVAILABLE':
            return False, "Book not available"

        # Update book status
        cur.execute("UPDATE books SET status = 'BORROWED' WHERE barcode = %s", (book_barcode,))
        
        # Create transaction
        cur.execute(
            "INSERT INTO transactions (user_id, book_barcode, status) VALUES (%s, %s, 'BORROWED')",
            (user_id, book_barcode)
        )
        conn.commit()
        return True, "Book borrowed successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def return_book(user_id, book_barcode):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if book is borrowed by this user
        cur.execute("""
            SELECT id FROM transactions 
            WHERE user_id = %s AND book_barcode = %s AND status = 'BORROWED'
        """, (user_id, book_barcode))
        transaction = cur.fetchone()
        
        if not transaction:
            return False, "No active borrow record found for this book and user"

        # Update book status
        cur.execute("UPDATE books SET status = 'AVAILABLE' WHERE barcode = %s", (book_barcode,))
        
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
        SELECT t.borrow_date, t.return_date, t.status, b.title, b.author 
        FROM transactions t
        JOIN books b ON t.book_barcode = b.barcode
        WHERE t.user_id = %s
        ORDER BY t.borrow_date DESC
    """
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df
