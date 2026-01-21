
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.first()
    if user:
        print(f"User found: {user.username}")
    else:
        print("No users found.")
