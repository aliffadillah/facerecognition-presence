import os
from config.db_config import FACES_DIR

def create_directories():
    """Create necessary directories if they don't exist"""
    if not os.path.exists(FACES_DIR):
        os.makedirs(FACES_DIR)
        print(f"Created directory: {FACES_DIR}")