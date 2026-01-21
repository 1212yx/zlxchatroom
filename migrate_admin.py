import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'zlxchat.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check columns in admin_users
cursor.execute("PRAGMA table_info(admin_users)")
columns = [info[1] for info in cursor.fetchall()]

if 'is_super' not in columns:
    print("Adding 'is_super' column...")
    cursor.execute("ALTER TABLE admin_users ADD COLUMN is_super BOOLEAN DEFAULT 0")

if 'created_at' not in columns:
    print("Adding 'created_at' column...")
    cursor.execute("ALTER TABLE admin_users ADD COLUMN created_at DATETIME")

conn.commit()
conn.close()
print("Migration complete.")
