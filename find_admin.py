from app import create_app
from app.models import AdminUser

app = create_app()

with app.app_context():
    admin = AdminUser.query.first()
    if admin:
        print(f"Found admin: {admin.username}")
    else:
        print("No admin user found.")
