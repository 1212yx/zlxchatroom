from app import create_app, db
from app.models import Room, Message, room_members
from sqlalchemy import text

app = create_app()

with app.app_context():
    rooms_to_delete = ["成功", "无", "yes", "gj"]
    
    for room_name in rooms_to_delete:
        room = Room.query.filter_by(name=room_name).first()
        if room:
            print(f"Deleting room: {room.name} (ID: {room.id})")
            
            # 1. Delete associated messages first
            deleted_msgs = Message.query.filter_by(room_id=room.id).delete()
            print(f"  - Deleted {deleted_msgs} messages.")

            # 2. Delete room membership associations
            # Since room_members is a Table object, we use delete statement
            stmt = room_members.delete().where(room_members.c.room_id == room.id)
            db.session.execute(stmt)
            print(f"  - Deleted memberships.")
            
            # 3. Delete the room itself
            db.session.delete(room)
            print(f"  - Room deleted from session.")
        else:
            print(f"Room not found: {room_name}")
    
    try:
        db.session.commit()
        print("All changes committed successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error during commit: {e}")
