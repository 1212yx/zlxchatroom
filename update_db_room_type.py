from app import create_app, db
from app.models import Room
from sqlalchemy import text
import sqlite3
import os

app = create_app()

def update_db():
    with app.app_context():
        # Check if column exists
        try:
            basedir = os.path.abspath(os.path.dirname(__file__))
            db_path = os.path.join(basedir, 'database', 'zlxchat.db')
            print(f"Database path: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if column exists in rooms table
            cursor.execute("PRAGMA table_info(rooms)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'room_type' not in columns:
                print("Adding room_type column to rooms table...")
                cursor.execute("ALTER TABLE rooms ADD COLUMN room_type VARCHAR(20) DEFAULT 'group'")
                conn.commit()
                print("Column added successfully.")
            else:
                print("Column room_type already exists.")
                
            conn.close()
            
        except Exception as e:
            print(f"Error updating database: {e}")

if __name__ == '__main__':
    update_db()
