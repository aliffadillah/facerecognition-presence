import cv2
import os
from config.db_config import FACES_DIR

class FaceDetector:
    def __init__(self):
        # Load the Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def detect_faces(self, frame):
        """Detect faces in a frame and return their coordinates"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        return gray, faces
    
    def capture_user_faces(self, user_id, num_images=20):
        """Capture multiple face images for a new user"""
        # Create directory for the user
        user_dir = os.path.join(FACES_DIR, str(user_id))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            return False
        
        count = 0
        while count < num_images:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray, faces = self.detect_faces(frame)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                # Save the face image
                if count < num_images and len(faces) > 0:
                    face_img = gray[y:y+h, x:x+w]
                    face_filename = os.path.join(user_dir, f'face_{count}.jpg')
                    cv2.imwrite(face_filename, face_img)
                    count += 1
                    print(f"Captured image {count}/{num_images}")
            
            # Display counter
            cv2.putText(frame, f'Captured: {count}/{num_images}', (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('Capture Faces', frame)
            
            # Break on ESC key
            if cv2.waitKey(100) == 27:
                break
                
        cap.release()
        cv2.destroyAllWindows()
        return count > 0