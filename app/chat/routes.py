from flask import render_template, request, session, redirect, url_for
from . import chat
from app.extensions import sock, db
from app.models import WSServer
import json
from datetime import datetime

# In-memory store for connected clients: {room_id: set(ws)}
# Using set for O(1) removal, but ws objects need to be hashable. They usually are.
rooms = {}

# In-memory store for registered users: {username: {'password': password, 'nickname': nickname}}
users = {}

@chat.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('nickname') # Using 'nickname' field from login form as username
        password = request.form.get('password')
        server = request.form.get('server')
        
        if username and password and server:
            if username not in users:
                error = "该账号未注册，请先注册账号"
            elif users[username]['password'] != password:
                error = "账号或密码错误"
            else:
                session['user'] = users[username]['nickname'] # Store nickname in session for display
                session['username'] = username # Store username in session for identification
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
            if username in users:
                error = "该账号已被注册"
            elif password != confirm_password:
                error = "两次输入的密码不一致"
            else:
                users[username] = {'password': password, 'nickname': nickname}
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
    user = None
    room = None
    
    try:
        # Wait for first message which should be join
        data = ws.receive()
        if data:
            msg = json.loads(data)
            if msg.get('type') == 'join':
                user = msg.get('user')
                room = msg.get('room')
                
                if not user or not room:
                    return

                if room not in rooms:
                    rooms[room] = set()
                rooms[room].add(ws)
                
                # Broadcast join
                broadcast(room, {
                    'type': 'system', 
                    'content': f'{user} 加入了 {room}',
                    'timestamp': datetime.now().strftime('%H:%M')
                })
                
                # Main loop
                while True:
                    data = ws.receive()
                    if not data:
                        break
                        
                    msg = json.loads(data)
                    if msg.get('type') == 'chat':
                        broadcast(room, {
                            'type': 'chat',
                            'user': user,
                            'content': msg.get('content'),
                            'timestamp': datetime.now().strftime('%H:%M')
                        })
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        if room and room in rooms and ws in rooms[room]:
            rooms[room].remove(ws)
            if not rooms[room]:
                del rooms[room]
            else:
                broadcast(room, {
                    'type': 'system', 
                    'content': f'{user} 离开了',
                    'timestamp': datetime.now().strftime('%H:%M')
                })

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
