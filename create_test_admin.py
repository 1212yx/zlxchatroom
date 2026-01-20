from app import create_app, db
from app.models import AdminUser

app = create_app()

with app.app_context():
    if not AdminUser.query.filter_by(username='test_admin').first():
        admin = AdminUser(username='test_admin', nickname='Test Admin')
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        print("Created test_admin")
    else:
        print("test_admin already exists")
