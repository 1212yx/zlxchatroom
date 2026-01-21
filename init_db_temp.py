from app import create_app, db
from app.models import FriendRequest, GroupRequest

app = create_app()
with app.app_context():
    db.create_all()
    print("Database tables created successfully.")
