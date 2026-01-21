from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Checking ai_chat_sessions table:")
    try:
        result = db.session.execute(text("PRAGMA table_info(ai_chat_sessions)"))
        for row in result:
            print(row)
    except Exception as e:
        print(f"Error: {e}")

    print("\nChecking ai_chat_messages table:")
    try:
        result = db.session.execute(text("PRAGMA table_info(ai_chat_messages)"))
        for row in result:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
