import cv2
import os
import numpy as np
from PIL import Image
from config.db_config import FACES_DIR, TRAINER_FILE

class FaceTrainer:
    def __init__(self):
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    def train_face_recognizer(self):
        """Train the face recognizer with saved faces"""
        faces = []
        ids = []
        
        # Check if faces directory exists
        if not os.path.exists(FACES_DIR) or not os.listdir(FACES_DIR):
            print("No face data found for training")
            return False
        
        # Traverse all user directories
        for user_id in os.listdir(FACES_DIR):
            user_dir = os.path.join(FACES_DIR, str(user_id))
            if os.path.isdir(user_dir):
                for img_file in os.listdir(user_dir):
                    if img_file.endswith('.jpg'):
                        img_path = os.path.join(user_dir, img_file)
                        try:
                            # Read and convert image
                            pil_img = Image.open(img_path).convert('L')
                            img_np = np.array(pil_img, 'uint8')
                            
                            faces.append(img_np)
                            ids.append(int(user_id))
                        except Exception as e:
                            print(f"Error processing {img_path}: {e}")
        
        if not faces or not ids:
            print("No face data found for training")
            return False
        
        try:
            self.face_recognizer.train(faces, np.array(ids))
            self.face_recognizer.save(TRAINER_FILE)
            print("Face recognizer trained and saved")
            return True
        except Exception as e:
            print(f"Error training face recognizer: {e}")
            return False