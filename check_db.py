from app import create_app, db
from app.models import SensitiveWord, WarningLog
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    
    for table in ['sensitive_words', 'warning_logs']:
        if table in inspector.get_table_names():
            print(f"Table '{table}' exists.")
            columns = [c['name'] for c in inspector.get_columns(table)]
            print(f"Columns: {columns}")
        else:
            print(f"Table '{table}' does NOT exist.")

    # Try query
    try:
        words = SensitiveWord.query.all()
        print(f"SensitiveWord Query successful. Count: {len(words)}")
        logs = WarningLog.query.all()
        print(f"WarningLog Query successful. Count: {len(logs)}")
    except Exception as e:
        print(f"Query failed: {e}")
