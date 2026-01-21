import os
from app import create_app, db
from sqlalchemy import text

app = create_app('default')

# Ensure database directory exists
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'database')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print(f"Created database directory at {db_dir}")

with app.app_context():
    print("Creating all tables (including new 'friendships' table)...")
    db.create_all() 
    
    # Check if columns exist in friend_requests
    try:
        with db.engine.connect() as conn:
            # SQLite specific check
            result = conn.execute(text("PRAGMA table_info(friend_requests)"))
            columns = [row[1] for row in result]
            
            if 'hello_message' not in columns:
                print("Adding hello_message column...")
                conn.execute(text("ALTER TABLE friend_requests ADD COLUMN hello_message VARCHAR(256)"))
            else:
                print("hello_message column already exists.")
                
            if 'remark' not in columns:
                print("Adding remark column...")
                conn.execute(text("ALTER TABLE friend_requests ADD COLUMN remark VARCHAR(64)"))
            else:
                print("remark column already exists.")
                
            print("Database update completed.")
    except Exception as e:
        print(f"Error updating database: {e}")
