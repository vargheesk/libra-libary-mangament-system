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
        st.header("Add New Book (Bulk Mode)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            isbn = st.text_input("ISBN / Book ID")
            title = st.text_input("Book Title")
        
        with col2:
            author = st.text_input("Author")
            category = st.selectbox("Category", ["Fiction", "Non-Fiction", "Science", "History", "Technology", "Other"])
            quantity = st.number_input("Number of Copies", min_value=1, value=1, step=1)
            
        if st.button("Add Books & Generate Barcodes"):
            if isbn and title:
                success, barcodes = add_book(isbn, title, author, category, quantity)
                if success:
                    st.success(f"Successfully added {quantity} copies of '{title}'!")
                    
                    st.subheader("🖨️ Print Barcodes")
                    st.info("Download these barcodes and stick them on the books.")
                    
                    # Display Barcodes
                    cols = st.columns(3)
                    for i, code in enumerate(barcodes):
                        # Generate Barcode Image
                        import barcode
                        from barcode.writer import ImageWriter
                        from io import BytesIO
                        
                        # Create barcode object
                        EAN = barcode.get_barcode_class('code128')
                        ean = EAN(code, writer=ImageWriter())
                        
                        # Save to buffer
                        buffer = BytesIO()
                        ean.write(buffer)
                        
                        # Display in grid
                        with cols[i % 3]:
                            st.image(buffer, caption=code, use_container_width=True)
                            st.download_button(
                                label=f"Download {code}",
                                data=buffer.getvalue(),
                                file_name=f"{code}.png",
                                mime="image/png",
                                key=f"btn_{code}"
                            )
                else:
                    st.error("Failed to add books.")
            else:
                st.warning("ISBN and Title are required.")

if __name__ == "__main__":
    main()
