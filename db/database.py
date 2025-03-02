import psycopg2
from config.db_config import DB_CONFIG

def get_connection():
    """Establish and return a connection to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        print("Please ensure PostgreSQL is running and connection details are correct.")
        return None

def initialize_database():
    """Initialize database tables if they don't exist"""
    conn = get_connection()
    if not conn:
        return None, None
    
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        user_id VARCHAR(50) NOT NULL UNIQUE
    )
    ''')
    
    # Create attendance table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    conn.commit()
    
    return conn, cursor

def close_connection(conn, cursor=None):
    """Safely close the database connection and cursor"""
    if cursor:
        cursor.close()
    if conn:
        conn.close()