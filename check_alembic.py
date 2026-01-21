from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        result = db.session.execute(text("SELECT * FROM alembic_version"))
        for row in result:
            print(f"Current revision: {row[0]}")
    except Exception as e:
        print(f"Error reading alembic_version: {e}")
