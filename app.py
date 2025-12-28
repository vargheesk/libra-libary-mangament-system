import streamlit as st
import cv2
import numpy as np
from face_auth import FaceAuthenticator
from scanner import decode_barcode
from CRUD.db import get_all_users, borrow_book, return_book, get_user_history, get_book
import face_recognition
import pickle
import time

# Page Config
st.set_page_config(page_title="Libra Kiosk", layout="wide")

# Initialize Session State
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'action_mode' not in st.session_state:
    st.session_state.action_mode = None  # 'borrow' or 'return'

# Load known faces (cached)
@st.cache_resource
def load_known_faces():
    users = get_all_users()
    known_encodings = []
    known_ids = []
    known_names = []
    
    for user in users:
        uid, name, encoding_bytes = user
        if encoding_bytes:
            encoding = pickle.loads(encoding_bytes)
            known_encodings.append(encoding)
            known_ids.append(uid)
            known_names.append(name)
            
    return known_encodings, known_ids, known_names

known_encodings, known_ids, known_names = load_known_faces()
authenticator = FaceAuthenticator()

def main():
    st.title("📚 Libra Library Kiosk")

    # Sidebar
    st.sidebar.title("Navigation")
    if st.session_state.authenticated:
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.action_mode = None
            st.rerun()
    
    # --- AUTHENTICATION PHASE ---
    if not st.session_state.authenticated:
        st.header("👤 User Authentication")
        st.info("Please look at the camera to login.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            frame_placeholder = st.empty()
            msg_placeholder = st.empty()
            
            # Camera Loop
            start_auth = st.button("Start Camera", key="start_auth")
            
            if start_auth:
                cap = cv2.VideoCapture(0)
                stop_auth = st.button("Stop Camera", key="stop_auth")
                
                while cap.isOpened() and not stop_auth:
                    ret, frame = cap.read()
                    if not ret:
                        st.error("Failed to access camera.")
                        break
                    
                    # Liveness Check
                    face_found, is_live, ear = authenticator.process_frame(frame)
                    
                    # Draw info on frame
                    cv2.putText(frame, f"Liveness: {'PASS' if is_live else 'FAIL'} (EAR: {ear:.2f})", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if is_live else (0, 0, 255), 2)
                    
                    # Show frame
                    frame_placeholder.image(frame, channels="BGR")
                    
                    if is_live:
                        # Try Recognition
                        encoding = authenticator.get_face_encoding(frame)
                        if encoding is not None:
                            matches = face_recognition.compare_faces(known_encodings, encoding)
                            face_distances = face_recognition.face_distance(known_encodings, encoding)
                            
                            if True in matches:
                                best_match_index = np.argmin(face_distances)
                                if matches[best_match_index]:
                                    user_id = known_ids[best_match_index]
                                    user_name = known_names[best_match_index]
                                    
                                    msg_placeholder.success(f"Authenticated as {user_name}!")
                                    st.session_state.authenticated = True
                                    st.session_state.user = {'id': user_id, 'name': user_name}
                                    time.sleep(1) # Brief pause to show success
                                    break
                            else:
                                msg_placeholder.warning("Face not recognized.")
                    else:
                        msg_placeholder.info("Please blink to verify liveness.")
                    
                    if stop_auth:
                        break
                
                cap.release()
                if st.session_state.authenticated:
                    st.rerun()

    # --- DASHBOARD PHASE ---
    else:
        user = st.session_state.user
        st.header(f"Welcome, {user['name']}!")
        
        tab1, tab2 = st.tabs(["📖 Dashboard", "📜 History"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Take Book", use_container_width=True):
                    st.session_state.action_mode = 'borrow'
            with col2:
                if st.button("📤 Return Book", use_container_width=True):
                    st.session_state.action_mode = 'return'
            
            if st.session_state.action_mode:
                st.divider()
                st.subheader(f"{'Borrowing' if st.session_state.action_mode == 'borrow' else 'Returning'} Mode")
                
                # Barcode Scanner
                scan_placeholder = st.empty()
                res_placeholder = st.empty()
                
                cap = cv2.VideoCapture(0)
                stop_scan = st.button("Stop Scanning")
                
                while cap.isOpened() and not stop_scan:
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    barcode, b_type = decode_barcode(frame)
                    
                    # Draw box if barcode found
                    if barcode:
                        cv2.putText(frame, f"Detected: {barcode}", (10, 50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        
                        # Process Action
                        if st.session_state.action_mode == 'borrow':
                            success, msg = borrow_book(user['id'], barcode)
                        else:
                            success, msg = return_book(user['id'], barcode)
                            
                        if success:
                            res_placeholder.success(msg)
                        else:
                            res_placeholder.error(msg)
                            
                        # Pause to prevent multiple scans of same frame
                        scan_placeholder.image(frame, channels="BGR")
                        time.sleep(2) 
                        break # Stop after one successful/failed scan attempt per button press? 
                              # Or continue? Let's break to let user see result.
                    
                    scan_placeholder.image(frame, channels="BGR")
                
                cap.release()
                if stop_scan:
                    st.session_state.action_mode = None
                    st.rerun()

        with tab2:
            st.subheader("Transaction History")
            history = get_user_history(user['id'])
            if not history.empty:
                st.dataframe(history)
            else:
                st.info("No history found.")

if __name__ == "__main__":
    main()
