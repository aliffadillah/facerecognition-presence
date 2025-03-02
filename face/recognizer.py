import cv2
import os
from config.db_config import TRAINER_FILE
from db.models import record_attendance, get_user_name
from face.detector import FaceDetector
from face.trainer import FaceTrainer

class FaceRecognizer:
    def __init__(self):
        self.detector = FaceDetector()
        
        # Load the face recognizer
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Check if trainer file exists
        if os.path.exists(TRAINER_FILE):
            self.face_recognizer.read(TRAINER_FILE)
            self.model_loaded = True
        else:
            # If not, try to train it
            trainer = FaceTrainer()
            if trainer.train_face_recognizer():
                self.face_recognizer.read(TRAINER_FILE)
                self.model_loaded = True
            else:
                self.model_loaded = False
    
    def is_model_loaded(self):
        """Check if the face recognition model is loaded"""
        return self.model_loaded
    
    def perform_attendance(self):
        """Perform attendance using face recognition"""
        if not self.model_loaded:
            print("No trained model found. Please add users first.")
            return
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            return
        
        recognized_users = set()  # To track recognized users in this session
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray, faces = self.detector.detect_faces(frame)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                face_img = gray[y:y+h, x:x+w]
                
                try:
                    # Recognize the face
                    user_id, confidence = self.face_recognizer.predict(face_img)
                    
                    # Lower confidence is better in LBPH
                    if confidence < 70:  # Confidence threshold
                        name = get_user_name(str(user_id))
                        
                        if name:
                            # Record attendance if not already done
                            if str(user_id) not in recognized_users:
                                success = record_attendance(str(user_id))
                                if success:
                                    recognized_users.add(str(user_id))
                            
                            # Display name and confidence
                            cv2.putText(frame, f"{name} ({user_id})", (x, y-10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            cv2.putText(frame, f"Conf: {round(100-confidence)}%", (x, y+h+30), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        else:
                            cv2.putText(frame, "Unknown", (x, y-10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        # Unknown face
                        cv2.putText(frame, "Unknown", (x, y-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                except Exception as e:
                    print(f"Error in recognition: {e}")
            
            # Display instructions
            cv2.putText(frame, "Press 'ESC' to exit", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow('Attendance System', frame)
            
            # Break on ESC key
            if cv2.waitKey(1) == 27:
                break
                
        cap.release()
        cv2.destroyAllWindows()