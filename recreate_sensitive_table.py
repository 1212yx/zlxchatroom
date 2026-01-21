from app import create_app, db
from app.models import SensitiveWord
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Drop table
    db.session.execute(text('DROP TABLE IF EXISTS sensitive_words'))
    db.session.commit()
    print("Dropped table 'sensitive_words'")
    
    # Create table
    db.create_all()
    print("Recreated tables (including sensitive_words)")
