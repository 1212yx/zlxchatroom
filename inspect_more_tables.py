from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Checking rooms table...")
    result = db.session.execute(text("PRAGMA table_info(rooms)"))
    columns = [row[1] for row in result]
    print(columns)
    
    print("Checking ws_servers table...")
    result = db.session.execute(text("PRAGMA table_info(ws_servers)"))
    columns = [row[1] for row in result]
    print(columns)
