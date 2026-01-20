from flask import render_template, request, session, redirect, url_for
from . import chat
from app.extensions import sock, db
from app.models import WSServer, db
from app.models import User, Room, Message
import json
from datetime import datetime

# In-memory store for connected clients: {room_id: set(ws)}
# Using set for O(1) removal, but ws objects need to be hashable. They usually are.
rooms = {}
# Mapping from ws object to username for tracking who is who
ws_user_map = {}

@chat.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username') # Using 'username' field from login form
        password = request.form.get('password')
        server = request.form.get('server')
        
        if username and password and server:
            user = User.query.filter_by(username=username).first()
            
            if not user:
                error = "该账号未注册，请先注册账号"
            elif not user.check_password(password):
                error = "账号或密码错误"
            else:
                session['user'] = user.nickname # Store nickname in session for display
                session['username'] = user.username # Store username in session for identification
                session['server'] = server
                return redirect(url_for('chat.home'))
            
    # 获取所有激活的服务器
    servers = WSServer.query.filter_by(is_active=True).all()
    return render_template('chat/login.html', error=error, servers=servers)

@chat.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        nickname = request.form.get('nickname')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if username and nickname and password and confirm_password:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = "该账号已被注册"
            elif password != confirm_password:
                error = "两次输入的密码不一致"
            else:
                new_user = User(username=username, nickname=nickname)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('chat.login'))
        else:
            error = "请填写所有字段"

    return render_template('chat/register.html', error=error)

@chat.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('chat.login'))
    return render_template('chat/chat.html', user=session['user'], server=session['server'])

@chat.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('chat.login'))

@sock.route('/ws', bp=chat)
def websocket(ws):
    username = session.get('username')
    user_obj = User.query.filter_by(username=username).first() if username else None
    
    user = None
    room = None
    room_obj = None
    
    try:
        # Wait for first message which should be join
        data = ws.receive()
        if data:
            msg = json.loads(data)
            if msg.get('type') == 'join':
                room = msg.get('room')
                # Trust session nickname if available, else use msg
                user = user_obj.nickname if user_obj else msg.get('user')
                
                if not user or not room:
                    return

                # DB: Ensure Room exists
                room_obj = Room.query.filter_by(name=room).first()
                if not room_obj:
                    room_obj = Room(name=room)
                    if user_obj:
                        room_obj.creator_id = user_obj.id
                    db.session.add(room_obj)
                    db.session.commit()

                if room not in rooms:
                    rooms[room] = set()
                rooms[room].add(ws)
                ws_user_map[ws] = user
                
                # Send History
                if room_obj:
                    history = Message.query.filter_by(room_id=room_obj.id).order_by(Message.timestamp.asc()).limit(50).all()
                    for h_msg in history:
                         ws.send(json.dumps({
                            'type': 'chat',
                            'user': h_msg.author.nickname if h_msg.author else 'Unknown',
                            'content': h_msg.content,
                            'timestamp': h_msg.timestamp.strftime('%H:%M')
                         }))
                
                # Broadcast join
                broadcast(room, {
                    'type': 'system', 
                    'content': f'{user} 加入了 {room}',
                    'timestamp': datetime.now().strftime('%H:%M')
                })
                
                # Broadcast updated user list
                broadcast_user_list(room)
                
                # Main loop
                while True:
                    data = ws.receive()
                    if not data:
                        break
                        
                    msg = json.loads(data)
                    if msg.get('type') == 'chat':
                        content = msg.get('content')
                        if content:
                            # Save to DB
                            if user_obj and room_obj:
                                db_msg = Message(content=content, user_id=user_obj.id, room_id=room_obj.id)
                                db.session.add(db_msg)
                                db.session.commit()
                            
                            broadcast(room, {
                                'type': 'chat',
                                'user': user,
                                'content': content,
                                'timestamp': datetime.now().strftime('%H:%M')
                            })
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        if room and room in rooms and ws in rooms[room]:
            rooms[room].remove(ws)
            if ws in ws_user_map:
                del ws_user_map[ws]
                
            if not rooms[room]:
                del rooms[room]
            else:
                broadcast(room, {
                    'type': 'system', 
                    'content': f'{user} 离开了',
                    'timestamp': datetime.now().strftime('%H:%M')
                })
                # Broadcast updated user list
                broadcast_user_list(room)

def broadcast(room, message):
    if room in rooms:
        # Create a copy to avoid runtime error if set changes during iteration
        for client in list(rooms[room]):
            try:
                client.send(json.dumps(message))
            except Exception:
                # Remove dead client
                try:
                    rooms[room].remove(client)
                except:
                    pass

def broadcast_user_list(room):
    if room in rooms:
        # Get unique users in the room
        users_in_room = set()
        for client in rooms[room]:
            if client in ws_user_map:
                users_in_room.add(ws_user_map[client])
        
        message = {
            'type': 'users',
            'users': list(users_in_room),
            'count': len(users_in_room)
        }
        broadcast(room, message)
