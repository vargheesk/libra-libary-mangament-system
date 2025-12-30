from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
import cv2
import numpy as np
import face_recognition
import base64
import io
from PIL import Image
from db import get_all_user_encodings, get_user_session_data, process_borrow, process_return
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'kiosk_secure_key_999'

# --- FACE AUTH LOGIC ---

def verify_face(captured_image_base64):
    """Compares captured image against database encodings."""
    try:
        # Decode base64 image
        encoded_data = captured_image_base64.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Get encoding of the captured face
        captured_encodings = face_recognition.face_encodings(rgb_img)
        if not captured_encodings:
            return None, "No face detected"
            
        if len(captured_encodings) > 1:
            return None, "Multiple faces detected. Please make sure only YOU are in the frame."

        captured_enc = captured_encodings[0]
        
        # Get all encodings from DB
        known_users = get_all_user_encodings()
        if not known_users:
            return None, "No registered users found"
            
        known_encodings = [u[2] for u in known_users]
        
        # Compare
        matches = face_recognition.compare_faces(known_encodings, captured_enc, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, captured_enc)
        
        if True in matches:
            best_match_index = np.argmin(face_distances)
            user_id = known_users[best_match_index][0]
            user_name = known_users[best_match_index][1]
            return {"id": user_id, "name": user_name}, None
            
        return None, "Face not recognized"
    except Exception as e:
        return None, str(e)

# --- ROUTES ---

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    image_data = data.get('image')
    
    user, error = verify_face(image_data)
    
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return jsonify({"success": True, "name": user['name']})
    else:
        return jsonify({"success": False, "error": error})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    data = get_user_session_data(session['user_id'])
    return render_template('dashboard.html', name=data['name'], books=data['books'], now=datetime.now())

@app.route('/borrow', methods=['POST'])
def borrow():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"})
        
    barcode = request.form.get('barcode')
    success, message = process_borrow(session['user_id'], barcode)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/return/<barcode>')
def return_book(barcode):
    if 'user_id' not in session:
        return redirect(url_for('home'))
        
    try:
        process_return(barcode)
        flash(f'Book {barcode} returned successfully.', 'success')
    except Exception as e:
        flash(f'Error returning book: {str(e)}', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5001) # Running on port 5001 to avoid conflict with admin
