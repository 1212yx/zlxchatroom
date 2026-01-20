from app import create_app, db
from app.models import AdminUser

app = create_app()

with app.app_context():
    # 检查是否已存在
    admin = AdminUser.query.filter_by(username='admin').first()
    if not admin:
        print("Creating admin user...")
        u = AdminUser(username='admin')
        u.set_password('admin888')
        db.session.add(u)
        db.session.commit()
        print("Admin user created successfully: admin/admin888")
    else:
        print("Admin user already exists.")
