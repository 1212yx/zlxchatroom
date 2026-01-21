from app import create_app, db
from app.models import Message, Room
# from sqlalchemy import func # Don't import func, use db.func
import datetime
import traceback

app = create_app()
with app.app_context():
    try:
        print("--- Testing db.func Usage ---")
        today = datetime.datetime.now().date()
        day_str = today.strftime('%Y-%m-%d')
        # Use db.func exactly as in routes.py
        count = Message.query.filter(db.func.date(Message.timestamp) == day_str).count()
        print(f"db.func.date count: {count}")
        
        print("--- Testing Message Authors ---")
        messages = Message.query.all()
        for msg in messages:
            try:
                author = msg.author
                username = author.username if author else 'Unknown'
                # print(f"Msg {msg.id} author: {username}")
            except Exception as e:
                print(f"Error accessing author for msg {msg.id}: {e}")
                
        print("--- Testing Active Rooms Sorting ---")
        # Logic from routes.py
        active_rooms = []
        rooms = Room.query.all()
        for room in rooms:
            msg_count = room.messages.count()
            member_count = room.members.count()
            active_rooms.append({
                'name': room.name,
                'msg_count': msg_count,
                'member_count': member_count,
                'status': '活跃' if msg_count > 0 else '空闲'
            })
        active_rooms.sort(key=lambda x: x['msg_count'], reverse=True)
        print("Active rooms sorted successfully")
        
        print("--- Done ---")
            
    except Exception as e:
        print(f"Global Error: {e}")
        traceback.print_exc()
