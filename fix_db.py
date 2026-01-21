from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        print("Adding type column to rooms table...")
        db.session.execute(text("ALTER TABLE rooms ADD COLUMN type VARCHAR(20) DEFAULT 'group'"))
        db.session.commit()
        print("Success.")
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
