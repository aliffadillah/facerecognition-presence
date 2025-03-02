import datetime
from db.models import add_user, delete_user, get_attendance_records, export_to_csv
from db.database import initialize_database
from face.detector import FaceDetector
from face.recognizer import FaceRecognizer
from face.trainer import FaceTrainer
from utils.helpers import create_directories

class Menu:
    def __init__(self):
        # Initialize database
        conn, cursor = initialize_database()
        if not conn:
            print("Could not connect to database. Exiting...")
            self.db_initialized = False
        else:
            conn.close()
            self.db_initialized = True
            
        # Create necessary directories
        create_directories()
    
    def display_main_menu(self):
        """Display the main menu and handle user choices"""
        if not self.db_initialized:
            return
            
        while True:
            print("\n===== Face Recognition Attendance System =====")
            print("1. Perform Attendance")
            print("2. Add New User")
            print("3. View Attendance Records")
            print("4. Exit")
            
            choice = input("Enter your choice (1-4): ")
            
            if choice == '1':
                self.perform_attendance()
            elif choice == '2':
                self.add_new_user()
            elif choice == '3':
                self.view_attendance_records()
            elif choice == '4':
                print("Exiting system...")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def perform_attendance(self):
        """Handle attendance operation"""
        recognizer = FaceRecognizer()
        if not recognizer.is_model_loaded():
            print("No users added yet. Please add users first.")
            return
            
        recognizer.perform_attendance()
    
    def add_new_user(self):
        """Handle adding a new user"""
        name = input("Enter user name: ")
        user_id = input("Enter user ID: ")
        
        # Add user to database
        success = add_user(name, user_id)
        if success:
            print(f"Capturing face data for {name}...")
            detector = FaceDetector()
            if detector.capture_user_faces(user_id):
                print(f"User {name} ({user_id}) added successfully")
                # Retrain the recognizer
                trainer = FaceTrainer()
                trainer.train_face_recognizer()
            else:
                print("Failed to capture face data. User not added.")
                # Remove user from database
                delete_user(user_id)
    
    def view_attendance_records(self):
        """Handle viewing attendance records"""
        date = input("Enter date (YYYY-MM-DD) or press Enter for today: ")
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            
        records = get_attendance_records(date)
        
        if not records:
            print(f"No attendance records found for {date}")
        else:
            print(f"\nAttendance Records for {date}:")
            print("-" * 50)
            print(f"{'Name':<20} {'User ID':<10} {'Time':<10}")
            print("-" * 50)
            for record in records:
                name, user_id, time = record
                print(f"{name:<20} {user_id:<10} {time}")
            print("-" * 50)
            print(f"Total: {len(records)} records")
        
        # Option to export to CSV
        export = input("Export to CSV? (y/n): ")
        if export.lower() == 'y':
            export_to_csv(records, date)