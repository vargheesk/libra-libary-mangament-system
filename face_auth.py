import cv2
import mediapipe as mp
import face_recognition
import numpy as np
from scipy.spatial import distance as dist

class FaceAuthenticator:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Eye landmarks
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        
        # Liveness parameters
        self.EAR_THRESHOLD = 0.25  # Eye Aspect Ratio threshold for closed eyes
        self.BLINK_CONSEC_FRAMES = 2 # Number of frames eyes must be closed
        self.blink_counter = 0
        self.total_blinks = 0
        self.liveness_verified = False

    def eye_aspect_ratio(self, eye_points, landmarks):
        # landmarks is a list of (x, y) tuples
        # Vertical landmarks
        A = dist.euclidean(landmarks[eye_points[1]], landmarks[eye_points[5]])
        B = dist.euclidean(landmarks[eye_points[2]], landmarks[eye_points[4]])
        # Horizontal landmark
        C = dist.euclidean(landmarks[eye_points[0]], landmarks[eye_points[3]])
        
        ear = (A + B) / (2.0 * C)
        return ear

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        frame_h, frame_w, _ = frame.shape
        
        if results.multi_face_landmarks:
            mesh_points = np.array([
                np.multiply([p.x, p.y], [frame_w, frame_h]).astype(int) 
                for p in results.multi_face_landmarks[0].landmark
            ])
            
            left_ear = self.eye_aspect_ratio(self.LEFT_EYE, mesh_points)
            right_ear = self.eye_aspect_ratio(self.RIGHT_EYE, mesh_points)
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Check for blink
            if avg_ear < self.EAR_THRESHOLD:
                self.blink_counter += 1
            else:
                if self.blink_counter >= self.BLINK_CONSEC_FRAMES:
                    self.total_blinks += 1
                    self.liveness_verified = True
                self.blink_counter = 0
                
            return True, self.liveness_verified, avg_ear
        
        return False, False, 0.0

    def get_face_encoding(self, frame):
        # Convert to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb_frame, model="hog")
        encodings = face_recognition.face_encodings(rgb_frame, boxes)
        
        if encodings:
            return encodings[0]
        return None

    def reset(self):
        self.blink_counter = 0
        self.total_blinks = 0
        self.liveness_verified = False
