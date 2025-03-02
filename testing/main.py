import cv2
import os
import numpy as np
import datetime
import sqlite3
from PIL import Image

# Database initialization
def initialize_database():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        user_id TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Create attendance table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY,
        user_id TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    conn.commit()
    return conn, cursor

# Function to add user to database
def add_user(conn, cursor, name, user_id):
    try:
        cursor.execute('INSERT INTO users (name, user_id) VALUES (?, ?)', (name, user_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"User ID {user_id} already exists!")
        return False

# Function to record attendance
def record_attendance(conn, cursor, user_id):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Check if user already has attendance for today
    cursor.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?', (user_id, today))
    if cursor.fetchone():
        print(f"Attendance for user {user_id} already recorded today.")
        return False
    
    cursor.execute('INSERT INTO attendance (user_id, date, time) VALUES (?, ?, ?)', 
                   (user_id, today, current_time))
    conn.commit()
    
    # Get user name
    cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
    name = cursor.fetchone()[0]
    print(f"Attendance recorded for {name} ({user_id}) at {current_time}")
    return True

# Create directory for storing user face data
def create_directories():
    if not os.path.exists('faces'):
        os.makedirs('faces')

# Function to capture and save user's face images
def capture_user_faces(user_id):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Create directory for the user
    user_dir = os.path.join('faces', str(user_id))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return False
    
    count = 0
    while count < 20:  # Capture 20 images
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            # Save the face image
            if count < 20 and len(faces) > 0:
                face_img = gray[y:y+h, x:x+w]
                face_filename = os.path.join(user_dir, f'face_{count}.jpg')
                cv2.imwrite(face_filename, face_img)
                count += 1
                print(f"Captured image {count}/20")
        
        # Display counter
        cv2.putText(frame, f'Captured: {count}/20', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('Capture Faces', frame)
        
        # Break on ESC key
        if cv2.waitKey(100) == 27:
            break
            
    cap.release()
    cv2.destroyAllWindows()
    return count > 0

# Train the face recognizer with saved faces
def train_face_recognizer():
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    faces = []
    ids = []
    
    # Traverse all user directories
    for user_id in os.listdir('faces'):
        user_dir = os.path.join('faces', user_id)
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
        return None
    
    face_recognizer.train(faces, np.array(ids))
    face_recognizer.save('trainer.yml')
    print("Face recognizer trained and saved")
    return face_recognizer

# Function to perform attendance
def perform_attendance(conn, cursor):
    # Check if trainer file exists, if not, train first
    if not os.path.exists('trainer.yml'):
        print("No trained model found. Training now...")
        face_recognizer = train_face_recognizer()
        if face_recognizer is None:
            print("Cannot train face recognizer. Please add users first.")
            return
    else:
        face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        face_recognizer.read('trainer.yml')
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    recognized_users = set()  # To track recognized users in this session
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            face_img = gray[y:y+h, x:x+w]
            
            try:
                # Recognize the face
                user_id, confidence = face_recognizer.predict(face_img)
                
                # Lower confidence is better in LBPH
                if confidence < 70:  # Confidence threshold
                    # Get user name
                    cursor.execute('SELECT name FROM users WHERE user_id = ?', (str(user_id),))
                    result = cursor.fetchone()
                    
                    if result:
                        name = result[0]
                        
                        # Record attendance if not already done
                        if str(user_id) not in recognized_users:
                            success = record_attendance(conn, cursor, str(user_id))
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

# Main function
def main():
    # Initialize database and create directories
    conn, cursor = initialize_database()
    create_directories()
    
    while True:
        print("\n===== Face Recognition Attendance System =====")
        print("1. Perform Attendance")
        print("2. Add New User")
        print("3. View Attendance Records")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == '1':
            # First ensure the recognizer is trained
            if not os.path.exists('trainer.yml') and not os.listdir('faces'):
                print("No users added yet. Please add users first.")
                continue
            elif not os.path.exists('trainer.yml'):
                print("Training face recognizer...")
                train_face_recognizer()
                
            perform_attendance(conn, cursor)
            
        elif choice == '2':
            name = input("Enter user name: ")
            user_id = input("Enter user ID: ")
            
            # Add user to database
            success = add_user(conn, cursor, name, user_id)
            if success:
                print(f"Capturing face data for {name}...")
                if capture_user_faces(user_id):
                    print(f"User {name} ({user_id}) added successfully")
                    # Retrain the recognizer
                    train_face_recognizer()
                else:
                    print("Failed to capture face data. User not added.")
                    # Remove user from database
                    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                    conn.commit()
            
        elif choice == '3':
            date = input("Enter date (YYYY-MM-DD) or press Enter for today: ")
            if not date:
                date = datetime.datetime.now().strftime("%Y-%m-%d")
                
            # Fetch attendance records for the date
            cursor.execute('''
            SELECT users.name, users.user_id, attendance.time 
            FROM attendance 
            JOIN users ON attendance.user_id = users.user_id 
            WHERE attendance.date = ? 
            ORDER BY attendance.time
            ''', (date,))
            
            records = cursor.fetchall()
            
            if not records:
                print(f"No attendance records found for {date}")
            else:
                print(f"\nAttendance Records for {date}:")
                print("-" * 50)
                print(f"{'Name':<20} {'User ID':<10} {'Time':<10}")
                print("-" * 50)
                for record in records:
                    name, user_id, time = record
                    print(f"{name:<20} {user_id:<10} {time:<10}")
                print("-" * 50)
                print(f"Total: {len(records)} records")
            
        elif choice == '4':
            print("Exiting system...")
            break
            
        else:
            print("Invalid choice. Please try again.")
    
    conn.close()

if __name__ == "__main__":
    main()