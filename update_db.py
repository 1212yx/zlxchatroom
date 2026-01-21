
from app import create_app, db
from sqlalchemy import text

app = create_app('default')

with app.app_context():
    try:
        # Check if column exists
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(rooms)")).fetchall()
            columns = [row[1] for row in result]
            if 'type' not in columns:
                print("Adding 'type' column to rooms table...")
                conn.execute(text("ALTER TABLE rooms ADD COLUMN type VARCHAR(20) DEFAULT 'group'"))
                conn.commit()
                print("Column added successfully.")
            else:
                print("'type' column already exists.")
    except Exception as e:
        print(f"Error: {e}")
