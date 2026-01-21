from app import create_app, db
from app.models import Room

app = create_app('default')

with app.app_context():
    names_to_delete = ["最后一运行", "老天保佑"]
    for name in names_to_delete:
        room = Room.query.filter_by(name=name).first()
        if room:
            print(f"Deleting room: {name} (ID: {room.id})")
            db.session.delete(room)
        else:
            print(f"Room not found: {name}")
    
    db.session.commit()
    print("Done.")
