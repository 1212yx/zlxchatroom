from app import create_app, db
from app.models import Room, User
import random

app = create_app()

with app.app_context():
    # Ensure there is at least one user to be the creator
    creator = User.query.first()
    if not creator:
        creator = User(username='test_admin', email='admin@example.com')
        creator.set_password('123456')
        db.session.add(creator)
        db.session.commit()
        print("Created test user")

    # Create dummy rooms
    room_names = [
        "技术交流群", "闲聊灌水", "游戏开黑", "音乐分享", 
        "电影推荐", "读书会", "二次元聚集地", "编程互助",
        "美食鉴赏", "旅行日记", "萌宠天地", "数码发烧友",
        "情感树洞", "职场吐槽", "英语角", "考研加油站"
    ]

    for name in room_names:
        if not Room.query.filter_by(name=name).first():
            room = Room(
                name=name,
                description=f"这里是{name}，欢迎大家一起来聊天！",
                creator=creator,
                is_banned=random.choice([True, False]) if random.random() > 0.8 else False
            )
            db.session.add(room)
    
    db.session.commit()
    print(f"Created {len(room_names)} dummy rooms.")
