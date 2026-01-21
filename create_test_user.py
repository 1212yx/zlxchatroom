
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(username='user').first():
        user = User(username='user', nickname='测试用户')
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        print("Test user created: user/123456")
