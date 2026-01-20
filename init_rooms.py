
from app import create_app, db
from app.models import Room, User
import random

app = create_app()

with app.app_context():
    # 检查是否已有房间
    # if Room.query.count() == 0:
    print("Initializing rooms...")
    users = User.query.all()
    
    # 确保至少有一个用户
    if not users:
        print("No users found. Creating a default user.")
        user = User(username='test_user', email='test@example.com')
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        users = [user]

    # 更新现有房间的创建人（如果为空）
    existing_rooms = Room.query.filter(Room.creator_id == None).all()
    if existing_rooms:
        print(f"Updating {len(existing_rooms)} rooms with creators...")
        for room in existing_rooms:
            room.creator = random.choice(users)
        db.session.commit()
    
    # 如果房间太少，补一些
    if Room.query.count() < 15:
        print("Creating more test rooms...")
        start_idx = Room.query.count() + 1
        for i in range(start_idx, 16):
            creator = random.choice(users)
            room = Room(name=f"聊天室 #{i}", description=f"这是第 {i} 个测试聊天室", creator=creator)
            db.session.add(room)
            
            # 随机添加成员
            members = random.sample(users, k=random.randint(0, min(len(users), 5)))
            for member in members:
                room.members.append(member)
        
        db.session.commit()
        print("Test rooms created.")
    else:
        print("Enough rooms exist.")
