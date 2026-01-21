from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    result = db.session.execute(text("PRAGMA table_info(users)"))
    print(f"{'CID':<5} {'Name':<20} {'Type':<10}")
    print("-" * 40)
    for row in result:
        # row is (cid, name, type, notnull, dflt_value, pk)
        print(f"{row[0]:<5} {row[1]:<20} {row[2]:<10}")
