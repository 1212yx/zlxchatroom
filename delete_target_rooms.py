from app import create_app, db
from app.models import Room

app = create_app('default')

with app.app_context():
    room_names = ['成功', '无']
    for name in room_names:
        room = Room.query.filter_by(name=name).first()
        if room:
            print(f"Deleting room: {room.name} (ID: {room.id})")
            db.session.delete(room)
        else:
            print(f"Room not found: {name}")
    
    try:
        db.session.commit()
        print("Deletion complete.")
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting rooms: {e}")
