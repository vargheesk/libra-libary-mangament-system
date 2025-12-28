import streamlit as st
import cv2
import numpy as np
import face_recognition
import pickle
from CRUD.db import add_user, add_book
from scanner import decode_barcode

st.set_page_config(page_title="Libra Admin", layout="wide")

def main():
    st.title("🛡️ Libra Admin Panel")
    
    menu = ["Register User", "Add Book"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Register User":
        st.header("Register New User")
        
        name = st.text_input("Full Name")
        
        method = st.radio("Input Method", ["Webcam Capture", "Upload Image"])
        
        img_buffer = None
        
        if method == "Webcam Capture":
            img_buffer = st.camera_input("Take a picture")
        else:
            img_buffer = st.file_uploader("Upload an image", type=['jpg', 'png', 'jpeg'])
            
        if st.button("Register"):
            if name and img_buffer:
                # Convert to bytes
                bytes_data = img_buffer.getvalue()
                
                # Convert to numpy array for cv2/face_recognition
                file_bytes = np.asarray(bytearray(bytes_data), dtype=np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                encodings = face_recognition.face_encodings(rgb_image)
                
                if encodings:
                    encoding_bytes = pickle.dumps(encodings[0])
                    user_id = add_user(name, encoding_bytes)
                    if user_id:
                        st.success(f"User {name} registered successfully! ID: {user_id}")
                    else:
                        st.error("Database error.")
                else:
                    st.error("No face detected in the image.")
            else:
                st.warning("Please provide both name and image.")
                
    elif choice == "Add Book":
        st.header("Add New Book")
        
        col1, col2 = st.columns(2)
        
        with col1:
            barcode_val = st.text_input("Barcode (Scan or Type)")
            
            # Optional: Live Scanner for adding books
            if st.checkbox("Use Camera to Scan Barcode"):
                cap = cv2.VideoCapture(0)
                frame_placeholder = st.empty()
                if st.button("Scan Now"):
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret: break
                        
                        code, _ = decode_barcode(frame)
                        frame_placeholder.image(frame, channels="BGR")
                        
                        if code:
                            barcode_val = code
                            st.success(f"Scanned: {code}")
                            break
                    cap.release()
        
        with col2:
            title = st.text_input("Book Title")
            author = st.text_input("Author")
            
        if st.button("Add Book"):
            if barcode_val and title:
                if add_book(barcode_val, title, author):
                    st.success(f"Book '{title}' added successfully!")
                else:
                    st.error("Failed to add book (maybe barcode exists?)")
            else:
                st.warning("Barcode and Title are required.")

if __name__ == "__main__":
    main()
