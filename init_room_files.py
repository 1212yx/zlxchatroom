from app import create_app, db
from app.models import RoomFile, User, Room
import random
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # 1. 创建表
    # 注意：db.create_all() 只会创建数据库中不存在的表，不会修改已存在的表。
    # 由于 RoomFile 是新表，所以这样是安全的。
    db.create_all()
    print("Database tables checked/created.")

    # 2. 检查是否有数据，如果没有则生成测试数据
    if RoomFile.query.count() == 0:
        print("Generating mock data for RoomFile...")
        
        users = User.query.all()
        rooms = Room.query.all()
        
        if not users or not rooms:
            print("No users or rooms found. Skipping mock data generation.")
        else:
            file_types = ['jpg', 'png', 'pdf', 'docx', 'xlsx', 'zip', 'txt']
            
            for _ in range(20): # 生成20个文件记录
                user = random.choice(users)
                room = random.choice(rooms)
                ftype = random.choice(file_types)
                fsize = random.randint(1024, 1024 * 1024 * 5) # 1KB to 5MB
                
                # 模拟文件名
                ts = int(datetime.utcnow().timestamp())
                filename = f"{ftype}_file_{ts}.{ftype}"
                original_filename = f"Project_Doc_{random.randint(1, 100)}.{ftype}"
                
                file_record = RoomFile(
                    filename=filename,
                    original_filename=original_filename,
                    file_size=fsize,
                    file_type=ftype,
                    file_path=f"uploads/files/{filename}", # 模拟路径
                    user_id=user.id,
                    room_id=room.id,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )
                db.session.add(file_record)
            
            db.session.commit()
            print("Mock data generated successfully.")
    else:
        print("RoomFile data already exists.")
