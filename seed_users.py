import os
import cv2
import face_recognition
import pickle
import numpy as np
from CRUD.db import add_user

FACES_DIR = "Faces"

def seed_users():
    if not os.path.exists(FACES_DIR):
        print(f"Directory {FACES_DIR} not found.")
        return

    print("Seeding users from Faces directory...")
    
    for filename in os.listdir(FACES_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            name = os.path.splitext(filename)[0]
            path = os.path.join(FACES_DIR, filename)
            
            print(f"Processing {name}...")
            try:
                # Load with OpenCV to resize if needed
                image = cv2.imread(path)
                if image is None:
                    print(f"Could not read {filename}")
                    continue
                
                # Resize if too large (e.g., width > 800)
                height, width = image.shape[:2]
                if width > 800:
                    scale = 800 / width
                    image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
                
                # Convert to RGB
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Get encodings
                encodings = face_recognition.face_encodings(rgb_image)
                
                if encodings:
                    encoding = encodings[0]
                    encoding_bytes = pickle.dumps(encoding)
                    
                    user_id = add_user(name, encoding_bytes)
                    if user_id:
                        print(f"Added user: {name} (ID: {user_id})")
                    else:
                        print(f"Failed to add user: {name}")
                else:
                    print(f"No face found in {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    seed_users()
