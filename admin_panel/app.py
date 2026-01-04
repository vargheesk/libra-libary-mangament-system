from flask import Flask, render_template, request, redirect, url_for, flash, send_file
# import os
# import cv2
# import numpy as np
import face_recognition
import pickle
from datetime import datetime
import io
import barcode
from barcode.writer import ImageWriter
from db import (
    get_stats, get_all_users, add_user, delete_user, update_user, get_user,
    get_all_books, add_book_bulk, delete_book, update_book, get_book,
    get_book_copies, delete_copy
)

app = Flask(__name__)
app.secret_key = 'supersecretkey' 


@app.context_processor
def inject_globals():
    return dict(get_user=get_user)

# --- ROUTES ---

@app.route('/')
def index():
    stats = get_stats()
    print("--------stats-----------")
    print()
    print(stats)
    print()
    print("-------------------------")
    return render_template('index.html', stats=stats, now=datetime.now())

# --- USER ROUTES ---

@app.route('/users')
def users_list():
    users = get_all_users()
    print("--------users-----------")
    print(users)
    print()
    print("-------------------------")
    return render_template('users/list.html', users=users, now=datetime.now())

@app.route('/users/add', methods=['GET', 'POST'])
def users_add():
    if request.method == 'POST':
        name = request.form.get('name')
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        address = request.form.get('address')
        file = request.files.get('photo')
        print("--------file-----------")
        print()
        print(file)
        print()
        print("-------------------------")
        
        
            
        
        image = face_recognition.load_image_file(file)
        encodings = face_recognition.face_encodings(image)
        print("--------encodings-----------")
        print()
        print(encodings)
        print()
        print("-------------------------")
        print(len(encodings))
        
        if len(encodings) == 0:
            flash('No face detected in the photo. Please try another one.', 'error')
            return redirect(request.url)
        
        if len(encodings) > 1:
            flash('Multiple faces detected. Please try another photo.', 'error')
            return redirect(request.url)
            
        encoding_bytes = pickle.dumps(encodings[0])
        
        try:
            add_user(name, encoding_bytes, dob, phone, address)
            flash('User registered successfully!', 'success')
            return redirect(url_for('users_list'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            
    return render_template('users/add.html', now=datetime.now())

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def users_edit(id):
    print("--------id-----------")
    print()
    print(id)
    print()
    print("-------------------------")
    user = get_user(id)
    print(user)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('users_list'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        address = request.form.get('address')
        try:
            update_user(id, name, dob, phone, address)
            flash('User updated successfully!', 'success')
            return redirect(url_for('users_list'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            
    return render_template('users/edit.html', user=user, now=datetime.now())

@app.route('/users/delete/<int:id>', methods=['POST'])
def users_delete(id):
    print("--------id-----------")
    print()
    print(id)
    print()
    print("-------------------------")
    try:
        delete_user(id)
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash('Could not delete user. They might have active transactions.', 'error')
    return redirect(url_for('users_list'))

# --- BOOK ROUTES ---

@app.route('/books')
def books_list():
    books = get_all_books()
    print("--------books-----------")
    print()
    print(books)
    print()
    for book in books:
        print(book)
    print("-------------------------")
    return render_template('books/list.html', books=books, now=datetime.now())

@app.route('/books/add', methods=['GET', 'POST'])
def books_add():
    if request.method == 'POST':
        isbn = request.form.get('isbn')
        title = request.form.get('title')
        author = request.form.get('author')
        category = request.form.get('category')
        quantity = int(request.form.get('quantity', 1))
        
        if not isbn or not title:
            flash('ISBN and Title are required!', 'error')
            return redirect(request.url)
            
        try:
            success, barcodes = add_book_bulk(isbn, title, author, category, quantity)
            print("--------success, barcodes-----------")
            print()
            print(success, barcodes)
            print()
            print("-------------------------")
            if success:
                flash(f'Added {quantity} copies and generated barcodes.', 'success')
                # Return back with barcodes or redirect
                return render_template('books/barcodes.html', barcodes=barcodes, title=title)
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            
    return render_template('books/add.html')

@app.route('/books/edit/<isbn>', methods=['GET', 'POST'])
def books_edit(isbn):
    print("--------isbn-----------")
    print()
    print(isbn)
    print()
    print("-------------------------")
    book = get_book(isbn)
    print("--------book-----------")
    print()
    print(book)
    print()
    print("-------------------------")
    if not book:
        flash('Book not found!', 'error')
        return redirect(url_for('books_list'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        category = request.form.get('category')
        try:
            update_book(isbn, title, author, category)
            flash('Book updated successfully!', 'success')
            return redirect(url_for('books_list'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            
    return render_template('books/edit.html', book=book)

@app.route('/books/delete/<isbn>', methods=['POST'])
def books_delete(isbn):
    print("--------isbn-----------")
    print()
    print(isbn)
    print()
    print("-------------------------")
    try:
        delete_book(isbn)
        flash('Book deleted successfully!', 'success')
    except Exception as e:
        flash('Could not delete book. Some copies might be borrowed.', 'error')
    return redirect(url_for('books_list'))

@app.route('/books/copies/<isbn>')
def books_copies(isbn):
    print("--------isbn-----------")
    print()
    print(isbn)
    print()
    print("-------------------------")
    book = get_book(isbn)
    print("--------book-----------")
    print()
    print(book)
    print()
    print("-------------------------")
    copies = get_book_copies(isbn)
    print("--------copies-----------")
    print()
    print(copies)
    print()
    print("-------------------------")
    return render_template('books/copies.html', book=book, copies=copies)

@app.route('/books/delete_copy/<barcode_val>')
def books_delete_copy(barcode_val):
    print("--------barcode_val-----------")
    print()
    print(barcode_val)
    print()
    print("-------------------------")
    isbn = barcode_val.split('-')[0]
    print("--------isbn-----------")
    print()
    print(isbn)
    print()
    print("-------------------------")
    try:
        delete_copy(barcode_val)
        flash(f'Copy {barcode_val} deleted.', 'success')
    except Exception as e:
        flash('Could not delete copy. It might have transaction history.', 'error')
    return redirect(url_for('books_copies', isbn=isbn))

@app.route('/generate_barcode/<barcode_val>')
def generate_barcode_img(barcode_val):
    print("--------barcode_val-----------")
    print()
    print(barcode_val)
    print()
    print("-------------------------")
    EAN = barcode.get_barcode_class('code128')
    print("--------EAN-----------")
    print()
    print(EAN)
    print()
    print("-------------------------")
    ean = EAN(barcode_val, writer=ImageWriter())
    print("--------ean-----------")
    print()
    print(ean)
    print()
    print("-------------------------")
    buffer = io.BytesIO()

    ean.write(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
