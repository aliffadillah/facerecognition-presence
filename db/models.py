import datetime
import csv
from db.database import get_connection, close_connection

def add_user(name, user_id):
    """Add a new user to the database"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (name, user_id) VALUES (%s, %s)', (name, user_id))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        print(f"Error adding user: {e}")
        success = False
    finally:
        close_connection(conn, cursor)
    
    return success

def delete_user(user_id):
    """Delete a user from the database"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        print(f"Error deleting user: {e}")
        success = False
    finally:
        close_connection(conn, cursor)
    
    return success

def record_attendance(user_id):
    """Record attendance for a user"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Check if user already has attendance for today
        cursor.execute('SELECT * FROM attendance WHERE user_id = %s AND date = %s', (user_id, today))
        if cursor.fetchone():
            print(f"Attendance for user {user_id} already recorded today.")
            close_connection(conn, cursor)
            return False
        
        cursor.execute('INSERT INTO attendance (user_id, date, time) VALUES (%s, %s, %s)', 
                      (user_id, today, current_time))
        conn.commit()
        
        # Get user name
        cursor.execute('SELECT name FROM users WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        if result:
            name = result[0]
            print(f"Attendance recorded for {name} ({user_id}) at {current_time}")
        
        success = True
    except Exception as e:
        conn.rollback()
        print(f"Error recording attendance: {e}")
        success = False
    finally:
        close_connection(conn, cursor)
    
    return success

def get_user_name(user_id):
    """Get a user's name by their ID"""
    conn = get_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT name FROM users WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        name = result[0] if result else None
    except Exception as e:
        print(f"Error getting user name: {e}")
        name = None
    finally:
        close_connection(conn, cursor)
    
    return name

def get_attendance_records(date=None):
    """Get attendance records for a specific date"""
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT users.name, users.user_id, attendance.time 
        FROM attendance 
        JOIN users ON attendance.user_id = users.user_id 
        WHERE attendance.date = %s 
        ORDER BY attendance.time
        ''', (date,))
        
        records = cursor.fetchall()
    except Exception as e:
        print(f"Error getting attendance records: {e}")
        records = []
    finally:
        close_connection(conn, cursor)
    
    return records

def export_to_csv(records, date):
    """Export attendance records to a CSV file"""
    if not records:
        print("No records to export.")
        return False
    
    filename = f"attendance_{date}.csv"
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Name', 'User ID', 'Time'])
            for record in records:
                writer.writerow(record)
        
        print(f"Attendance exported to {filename}")
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False