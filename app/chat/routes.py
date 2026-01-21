from flask import render_template, request, session, redirect, url_for, jsonify
from . import chat
from app.extensions import sock, db
from app.models import WSServer, db
from app.models import User, Room, Message, Sticker, FriendRequest, GroupRequest, AIModel, room_members
import json
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
from app.bot.core import get_bot_response
from app.chat.weather import get_weather_data, parse_weather_video
from app.chat.music import get_music_data

# Configure Uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_FILE_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z', 'mp3', 'mp4', 'wav', 'webm', 'ogg'}
UPLOAD_FOLDER = os.path.join('app', 'chat', 'static', 'uploads', 'stickers')
FILE_UPLOAD_FOLDER = os.path.join('app', 'chat', 'static', 'uploads', 'files')
AVATAR_UPLOAD_FOLDER = os.path.join('app', 'chat', 'static', 'uploads', 'avatars')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_general_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in (ALLOWED_EXTENSIONS | ALLOWED_FILE_EXTENSIONS)

# Ensure upload directories exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(FILE_UPLOAD_FOLDER):
    os.makedirs(FILE_UPLOAD_FOLDER)
if not os.path.exists(AVATAR_UPLOAD_FOLDER):
    os.makedirs(AVATAR_UPLOAD_FOLDER)

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
    
    username = session.get('username')
    user_obj = User.query.filter_by(username=username).first()
    avatar = user_obj.avatar if user_obj else None
    
    return render_template('chat/chat.html', user=session['user'], username=username, server=session['server'], avatar=avatar, current_user_obj_id=user_obj.id if user_obj else 0)

@chat.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('chat.login'))

@chat.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
         return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
        
    nickname = request.form.get('nickname')
    old_nickname = user.nickname
    
    if nickname:
        user.nickname = nickname
        session['user'] = nickname
        
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"avatar_{user.id}_{int(datetime.now().timestamp())}_{file.filename}")
            file.save(os.path.join(AVATAR_UPLOAD_FOLDER, filename))
            avatar_url = url_for('chat.static', filename=f'uploads/avatars/{filename}')
            user.avatar = avatar_url
            
    db.session.commit()
    
    # Broadcast update
    room = session.get('server')
    if room:
        # Update ws_user_map
        for ws, nick in list(ws_user_map.items()):
            if nick == old_nickname:
                 ws_user_map[ws] = user.nickname
                 
        broadcast(room, {
            'type': 'profile_update',
            'username': user.username,
            'nickname': user.nickname,
            'avatar': user.avatar,
            'old_nickname': old_nickname
        })
        broadcast_user_list(room)
        
    return jsonify({'success': True, 'nickname': user.nickname, 'avatar': user.avatar})

@chat.route('/upload_sticker', methods=['POST'])
def upload_sticker():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件上传'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Generate unique filename to avoid collisions
        unique_filename = str(uuid.uuid4()) + "_" + filename
        file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
        
        # Return the URL for the uploaded file
        file_url = url_for('chat.static', filename=f'uploads/stickers/{unique_filename}')
        
        # Save to DB
        user = User.query.filter_by(username=session['username']).first()
        if user:
            sticker = Sticker(
                url=file_url,
                filename=filename,
                user=user
            )
            db.session.add(sticker)
            db.session.commit()
        
        return jsonify({'success': True, 'url': file_url})
    
    return jsonify({'success': False, 'message': '不支持的文件类型'}), 400

@chat.route('/get_stickers')
def get_stickers():
    if 'username' not in session:
        return jsonify({'success': False, 'stickers': []})
        
    user = User.query.filter_by(username=session['username']).first()
    if not user:
         return jsonify({'success': False, 'stickers': []})
         
    stickers = Sticker.query.filter_by(user_id=user.id).order_by(Sticker.created_at.asc()).all()
    return jsonify({
        'success': True, 
        'stickers': [{'id': s.id, 'url': s.url} for s in stickers]
    })

@chat.route('/delete_sticker', methods=['POST'])
def delete_sticker():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    data = request.get_json()
    sticker_url = data.get('url')
    
    user = User.query.filter_by(username=session['username']).first()
    
    if sticker_url and user:
        sticker = Sticker.query.filter_by(url=sticker_url, user_id=user.id).first()
        if sticker:
            # Optionally remove file from disk here if needed
            db.session.delete(sticker)
            db.session.commit()
            return jsonify({'success': True})
            
    return jsonify({'success': False, 'message': '表情不存在'})

@chat.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件上传'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
        
    if file and allowed_general_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        
        # Determine folder based on type, or just put all in files
        file.save(os.path.join(FILE_UPLOAD_FOLDER, unique_filename))
        
        file_url = url_for('chat.static', filename=f'uploads/files/{unique_filename}')
        
        return jsonify({'success': True, 'url': file_url})
    
    return jsonify({'success': False, 'message': '不支持的文件类型'}), 400

@chat.route('/search_user', methods=['POST'])
def search_user():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    username = request.form.get('username')
    if not username:
        return jsonify({'success': False, 'message': '请输入用户名'})
        
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'success': True, 'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'avatar': user.avatar or ''
        }})
    return jsonify({'success': False, 'message': '用户不存在'})

@chat.route('/search_group', methods=['POST'])
def search_group():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    keyword = request.form.get('keyword')
    if not keyword:
        return jsonify({'success': False, 'message': '请输入群号或群名称'})
        
    # Try searching by ID or Name
    group = None
    if keyword.isdigit():
         group = Room.query.filter_by(id=int(keyword)).first()
    
    if not group:
        group = Room.query.filter_by(name=keyword).first()
        
    if group:
        return jsonify({'success': True, 'group': {
            'id': group.id,
            'name': group.name,
            'description': group.description or '暂无简介',
            'member_count': group.members.count()
        }})
    return jsonify({'success': False, 'message': '群聊不存在'})

@chat.route('/send_friend_request', methods=['POST'])
def send_friend_request():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    receiver_id = request.form.get('user_id')
    if not receiver_id:
        return jsonify({'success': False, 'message': '参数错误'})
        
    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'success': False, 'message': '用户不存在'})
    
    current_user_obj = User.query.filter_by(username=session.get('username')).first()
    
    if current_user_obj.id == int(receiver_id):
        return jsonify({'success': False, 'message': '不能添加自己为好友'})

    # Check existing request
    existing_request = FriendRequest.query.filter_by(
        sender_id=current_user_obj.id,
        receiver_id=receiver_id,
        status='pending'
    ).first()
    
    if existing_request:
        return jsonify({'success': False, 'message': '已发送过申请'})

    hello_message = request.form.get('hello_message')
    remark = request.form.get('remark')

    new_request = FriendRequest(
        sender_id=current_user_obj.id, 
        receiver_id=receiver_id,
        hello_message=hello_message,
        remark=remark
    )
    db.session.add(new_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '好友申请已发送'})

@chat.route('/get_friend_requests')
def get_friend_requests():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    current_user_obj = User.query.filter_by(username=session.get('username')).first()
    
    # Get pending requests received by current user
    requests = FriendRequest.query.filter_by(
        receiver_id=current_user_obj.id,
        status='pending'
    ).order_by(FriendRequest.created_at.desc()).all()
    
    result = []
    for req in requests:
        sender = User.query.get(req.sender_id)
        result.append({
            'id': req.id,
            'sender': {
                'id': sender.id,
                'username': sender.username,
                'nickname': sender.nickname,
                'avatar': sender.avatar or ''
            },
            'hello_message': req.hello_message or '无验证信息',
            'remark': req.remark,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M')
        })
        
    return jsonify({'success': True, 'requests': result})

@chat.route('/handle_friend_request', methods=['POST'])
def handle_friend_request():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    request_id = request.form.get('request_id')
    action = request.form.get('action') # 'accept' or 'reject'
    
    if not request_id or not action:
        return jsonify({'success': False, 'message': '参数错误'})
        
    req = FriendRequest.query.get(request_id)
    if not req:
        return jsonify({'success': False, 'message': '申请不存在'})
        
    current_user_obj = User.query.filter_by(username=session.get('username')).first()
    
    if req.receiver_id != current_user_obj.id:
        return jsonify({'success': False, 'message': '无权操作'})
        
    if action == 'accept':
        req.status = 'accepted'
        # Add to friends list
        sender = User.query.get(req.sender_id)
        
        # Check if already friends (just in case)
        if sender not in current_user_obj.friends:
            current_user_obj.friends.append(sender)
            sender.friends.append(current_user_obj) # Bi-directional friendship
            
        # Create Private Chat Room
        # Naming convention: private_{min_id}_{max_id}
        u1_id = min(current_user_obj.id, sender.id)
        u2_id = max(current_user_obj.id, sender.id)
        room_name = f"private_{u1_id}_{u2_id}"
        
        room = Room.query.filter_by(name=room_name).first()
        if not room:
            room = Room(name=room_name, is_banned=False)
            db.session.add(room)
            db.session.commit() # Commit to get ID
            
        # Ensure members
        if current_user_obj not in room.members:
            room.members.append(current_user_obj)
        if sender not in room.members:
            room.members.append(sender)
            
        # Send Welcome Message
        welcome_msg = Message(
            content="我们已成功添加为好友，现在可以开始聊天啦～",
            user_id=current_user_obj.id,
            room_id=room.id
        )
        db.session.add(welcome_msg)
            
        db.session.commit()
        return jsonify({'success': True, 'message': '已同意好友申请'})
        
    elif action == 'reject':
        req.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': '已拒绝好友申请'})
        
    return jsonify({'success': False, 'message': '无效操作'})

@chat.route('/get_friends')
def get_friends():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
        
    friends_list = []
    for friend in user.friends:
        u1_id = min(user.id, friend.id)
        u2_id = max(user.id, friend.id)
        room_name = f"private_{u1_id}_{u2_id}"
        
        friends_list.append({
            'id': friend.id,
            'username': friend.username,
            'nickname': friend.nickname,
            'avatar': friend.avatar or '',
            'status': 'offline', # TODO: Implement online status check
            'room': room_name
        })
        
    return jsonify({'success': True, 'friends': friends_list})

@chat.route('/get_chat_list')
def get_chat_list():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    user = User.query.filter_by(username=session.get('username')).first()
    
    # Get rooms user is member of
    # We want to show latest message info
    chats = []
    
    # 1. Add Default Server Room (if applicable, or handled separately)
    # The current 'home' logic puts user in session['server'].
    # We can include it as a chat item.
    current_server = session.get('server')
    if current_server:
        chats.append({
            'type': 'group',
            'id': 'server',
            'name': current_server,
            'avatar': None, # Default icon
            'room': current_server,
            'last_message': '',
            'timestamp': ''
        })

    # 2. Private Chats & Joined Groups
    for room in user.rooms:
        # Determine display info
        display_name = room.name
        avatar = None
        chat_type = 'group'
        
        if room.name.startswith('private_'):
            # Find the other member
            other_member = None
            for m in room.members:
                if m.id != user.id:
                    other_member = m
                    break
            
            if other_member:
                display_name = other_member.nickname or other_member.username
                avatar = other_member.avatar
                chat_type = 'private'
            else:
                continue # Should not happen for valid private chats
        
        # Get last message
        last_msg = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.desc()).first()
        
        chats.append({
            'type': chat_type,
            'id': room.id,
            'name': display_name,
            'avatar': avatar,
            'room': room.name,
            'last_message': last_msg.content[:30] if last_msg else '',
            'timestamp': last_msg.timestamp.strftime('%H:%M') if last_msg else ''
        })
    
    # Sort by timestamp descending (if available)
    # chats.sort(key=lambda x: x['timestamp'], reverse=True) 
    # Note: timestamp format is HH:MM, might not be enough for correct sorting across days, 
    # but good enough for simple demo. Better to use raw datetime object for sorting.
    
    return jsonify({'success': True, 'chats': chats})

@chat.route('/create_group', methods=['POST'])
def create_group():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    name = request.form.get('name')
    if not name:
        return jsonify({'success': False, 'message': '群聊名称不能为空'}), 400
        
    # Check if name exists
    if Room.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': '群聊名称已存在'}), 400
        
    try:
        current_user = User.query.filter_by(username=session['username']).first()
        new_room = Room(name=name, creator=current_user, type='group')
        new_room.members.append(current_user)
        
        # Handle invited members
        members_json = request.form.get('members')
        if members_json:
            try:
                member_ids = json.loads(members_json)
                for mid in member_ids:
                    user = User.query.get(mid)
                    if user and user != current_user:
                        new_room.members.append(user)
            except Exception as e:
                print(f"Error adding members: {e}")
        
        db.session.add(new_room)
        db.session.commit()
        return jsonify({'success': True, 'room_id': new_room.id, 'name': new_room.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@chat.route('/join_group_by_id', methods=['POST'])
def join_group_by_id():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    group_id = request.form.get('group_id')
    if not group_id:
        return jsonify({'success': False, 'message': '请输入群号'})
        
    room = Room.query.get(group_id)
    if not room:
        return jsonify({'success': False, 'message': '群聊不存在'})
        
    if room.type != 'group':
        return jsonify({'success': False, 'message': '该房间不支持加入'})
        
    user = User.query.filter_by(username=session['username']).first()
    
    if user not in room.members:
        room.members.append(user)
        db.session.commit()
        
    return jsonify({'success': True, 'room_id': room.id, 'name': room.name})



@chat.route('/get_friend_details', methods=['POST'])
def get_friend_details():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    friend_id = request.form.get('user_id')
    if not friend_id:
        return jsonify({'success': False, 'message': '参数错误'})
        
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({'success': False, 'message': '用户不存在'})
        
    current_user_obj = User.query.filter_by(username=session.get('username')).first()
    
    # Try to find remark from FriendRequest
    # 1. I added them
    req = FriendRequest.query.filter_by(
        sender_id=current_user_obj.id, 
        receiver_id=friend.id, 
        status='accepted'
    ).first()
    
    remark = req.remark if req and req.remark else ''
    
    # Determine room name
    u1_id = min(current_user_obj.id, friend.id)
    u2_id = max(current_user_obj.id, friend.id)
    room_name = f"private_{u1_id}_{u2_id}"
    
    return jsonify({
        'success': True,
        'friend': {
            'id': friend.id,
            'username': friend.username,
            'nickname': friend.nickname,
            'avatar': friend.avatar or '',
            'remark': remark,
            'status': 'offline', # Placeholder
            'room': room_name
        }
    })

@chat.route('/share_friend_card', methods=['POST'])
def share_friend_card():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    target_room_name = request.form.get('target_room')
    friend_id = request.form.get('friend_id')
    
    if not target_room_name or not friend_id:
        return jsonify({'success': False, 'message': '参数错误'})
        
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({'success': False, 'message': '用户不存在'})
        
    current_user_obj = User.query.filter_by(username=session.get('username')).first()
    
    # Check if user is member of target room
    room = Room.query.filter_by(name=target_room_name).first()
    if not room:
         return jsonify({'success': False, 'message': '房间不存在'})
         
    if current_user_obj not in room.members:
        return jsonify({'success': False, 'message': '您不在该群聊中'})

    # Construct Message
    content = f"[名片] 昵称: {friend.nickname or friend.username}, 账号: {friend.username}"
    
    msg = Message(
        content=content,
        user_id=current_user_obj.id,
        room_id=room.id
    )
    db.session.add(msg)
    db.session.commit()
    
    # Broadcast
    if target_room_name in rooms:
        # Prepare JSON
        msg_data = json.dumps({
            'type': 'chat',
            'user': current_user_obj.nickname or current_user_obj.username,
            'username': current_user_obj.username,
            'avatar': current_user_obj.avatar,
            'content': content,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
        
        to_remove = set()
        for client in rooms[target_room_name]:
            try:
                client.send(msg_data)
            except:
                to_remove.add(client)
        
        for client in to_remove:
            rooms[target_room_name].discard(client)
            if client in ws_user_map:
                del ws_user_map[client]
                
    return jsonify({'success': True, 'message': '已发送名片'})

@chat.route('/send_group_request', methods=['POST'])
def send_group_request():
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
        
    group_id = request.form.get('group_id')
    if not group_id:
        return jsonify({'success': False, 'message': '参数错误'})
        
    group = Room.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'message': '群聊不存在'})
        
    current_user_obj = User.query.filter_by(username=session.get('username')).first()
    
    # Check if already member
    if current_user_obj in group.members:
        return jsonify({'success': False, 'message': '已在群聊中'})

    # Check existing request
    existing_request = GroupRequest.query.filter_by(
        user_id=current_user_obj.id,
        group_id=group_id,
        status='pending'
    ).first()
    
    if existing_request:
        return jsonify({'success': False, 'message': '已发送过申请'})

    new_request = GroupRequest(user_id=current_user_obj.id, group_id=group_id)
    db.session.add(new_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '入群申请已发送'})

@sock.route('/ws', bp=chat)
def websocket(ws):
    print("WebSocket connection started")
    username = session.get('username')
    
    # Pre-fetch user info and close session immediately to avoid holding connection
    user_id = None
    user_nickname = None
    
    if username:
        user_obj = User.query.filter_by(username=username).first()
        if user_obj:
            user_id = user_obj.id
            user_nickname = user_obj.nickname
    
    db.session.remove()
    
    user = None
    room = None
    room_id = None
    
    # Log Connect
    if user_obj:
        try:
            log = ActivityLog(user_id=user_obj.id, username=user_obj.username, action='login', content='上线')
            db.session.add(log)
            db.session.commit()
        except:
            db.session.rollback()
    
    try:
        # Wait for first message which should be join
        print("Waiting for join message...")
        data = ws.receive()
        print(f"Received data: {data}")
        if data:
            msg = json.loads(data)
            if msg.get('type') == 'join':
                room = msg.get('room')
                # Trust session nickname if available, else use msg
                user = user_nickname if user_nickname else msg.get('user')
                
                if not user or not room:
                    return

                # DB: Ensure Room exists
                # Start new session for room logic
                room_obj = Room.query.filter_by(name=room).first()
                if not room_obj:
                    room_obj = Room(name=room)
                    if user_id:
                        room_obj.creator_id = user_id
                    db.session.add(room_obj)
                    db.session.commit()
                
                room_id = room_obj.id

                if room not in rooms:
                    rooms[room] = set()
                rooms[room].add(ws)
                ws_user_map[ws] = user
                
                # Send History
                print("Sending history...")
                history_data = []
                if room_id:
                    history = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.desc()).limit(50).all()
                    history.reverse() # Show latest messages
                    for h_msg in history:
                         sender_name = h_msg.author.nickname if h_msg.author else 'Unknown'
                         # Try to determine sender for special messages if author is None
                         if not h_msg.author and h_msg.content.startswith('SPECIAL:'):
                             try:
                                 special_data = json.loads(h_msg.content[8:])
                                 msg_type = special_data.get('type')
                                 if msg_type == 'weather':
                                     sender_name = '小天气'
                                 elif msg_type.startswith('music'):
                                     sender_name = '小音乐'
                             except:
                                 pass
                         
                         # For bot response (if we decide to save it), we might need a way to identify it.
                         # For now, let's just send what we have.
                         
                         history_data.append({
                            'type': 'chat',
                            'user': sender_name,
                            'username': h_msg.author.username if h_msg.author else None,
                            'avatar': h_msg.author.avatar if h_msg.author else None,
                            'content': h_msg.content,
                            'timestamp': h_msg.timestamp.strftime('%H:%M'),
                            'is_history': True
                         })
                
                # Release session after fetching history
                db.session.remove()

                print(f"History items: {len(history_data)}")
                for h_msg in history_data:
                     ws.send(json.dumps(h_msg))
                print("History sent.")
                
                # Broadcast join
                print("Broadcasting join...")
                broadcast(room, {
                    'type': 'system', 
                    'content': f'{user} 加入了 {room}',
                    'timestamp': datetime.now().strftime('%H:%M')
                })
                
                # Log Join
                try:
                    log = ActivityLog(user_id=user_obj.id if user_obj else None, username=user, action='join_room', content=room)
                    db.session.add(log)
                    db.session.commit()
                except:
                    db.session.rollback()
                
                # Broadcast updated user list
                print("Broadcasting user list...")
                broadcast_user_list(room)
                
                # Main loop
                print("Entering main loop...")
                while True:
                    data = ws.receive()
                    if not data:
                        break
                        
                    msg = json.loads(data)
                    if msg.get('type') == 'chat':
                        content = msg.get('content')
                        if content:
                            # Start new session for message handling
                            current_user_obj = None
                            if user_id:
                                current_user_obj = User.query.get(user_id)
                                if current_user_obj:
                                    user = current_user_obj.nickname # Update local user variable
                            
                            # Check sensitive words
                            sensitive_words = SensitiveWord.query.all()
                            found_sensitive = None
                            for sw in sensitive_words:
                                if sw.word in content:
                                    found_sensitive = sw.word
                                    break
                            
                            if found_sensitive:
                                # Intercept and Log Warning
                                if user_obj and room_obj:
                                    warning = WarningLog(
                                        content=content,
                                        user_id=user_obj.id,
                                        room_id=room_obj.id,
                                        triggered_word=found_sensitive
                                    )
                                    db.session.add(warning)
                                    db.session.commit()
                                
                                # Notify sender only
                                ws.send(json.dumps({
                                    'type': 'system', 
                                    'content': f'系统拦截：您的消息包含敏感词 "{found_sensitive}"，发送失败。',
                                    'timestamp': datetime.now().strftime('%H:%M')
                                }))
                                # Skip broadcast and save
                                continue

                            # Save to DB
                            if user_id and room_id:
                                db_msg = Message(content=content, user_id=user_id, room_id=room_id)
                                db.session.add(db_msg)
                                db.session.commit()
                                
                                # Log Chat Activity
                                try:
                                    log = ActivityLog(user_id=user_obj.id, username=user, action='chat', content=content[:50]) # limit content length
                                    db.session.add(log)
                                    db.session.commit()
                                except:
                                    db.session.rollback()
                            
                            # Prepare broadcast data
                            broadcast_msg = {
                                'type': 'chat',
                                'user': user,
                                'username': current_user_obj.username if current_user_obj else None,
                                'avatar': current_user_obj.avatar if current_user_obj else None,
                                'content': content,
                                'timestamp': datetime.now().strftime('%H:%M')
                            }

                            # Check for Bot Trigger
                            if content.startswith('@小师妹'):
                                try:
                                    # Stream response
                                    broadcast(room, {'type': 'stream_start', 'user': '小师妹', 'timestamp': datetime.now().strftime('%H:%M')})
                                    full_response = ""
                                    # Remove trigger word
                                    query = content.replace('@小师妹', '').strip()
                                    for chunk in get_bot_response(query, user, room):
                                        broadcast(room, {
                                            'type': 'stream_chunk',
                                            'content': chunk,
                                            'user': '小师妹'
                                        })
                                        full_response += chunk
                                    
                                    broadcast(room, {'type': 'stream_end', 'user': '小师妹'})
                                    
                                    # Save Bot Response to DB (Persistence)
                                    if full_response and room_obj:
                                        # Use a special format to identify it's from Bot (since user_id is None)
                                        # Or just save text. History loader defaults to 'Unknown' -> we can patch loader to show '小师妹'
                                        # But let's use SPECIAL for consistency if possible, or just accept 'Unknown' for now.
                                        # Actually, better to just save it.
                                        bot_msg = Message(content=full_response, user_id=None, room_id=room_obj.id)
                                        db.session.add(bot_msg)
                                        db.session.commit()
                                        
                                except Exception as e:
                                    print(f"Bot Error: {e}")
                                    broadcast(room, {
                                        'type': 'chat',
                                        'user': 'System',
                                        'content': f"小师妹出错了: {str(e)}",
                                        'timestamp': datetime.now().strftime('%H:%M')
                                    })
                            
                            # Check for Weather Trigger
                            elif content.startswith('小天气'):
                                try:
                                    city = content.replace('小天气', '').strip()
                                    if not city:
                                        city = "北京"
                                    
                                    broadcast(room, {
                                        'type': 'chat', 
                                        'user': '小天气', 
                                        'content': f"正在查询 {city} 的天气...", 
                                        'timestamp': datetime.now().strftime('%H:%M')
                                    })

                                    data = get_weather_data(city)
                                    
                                    if 'error' in data:
                                        broadcast(room, {
                                            'type': 'chat',
                                            'user': '小天气',
                                            'content': f"查询失败: {data['error']}",
                                            'timestamp': datetime.now().strftime('%H:%M')
                                        })
                                    else:
                                        # Create Special Message for Persistence
                                        special_payload = {
                                            'type': 'weather',
                                            'data': data
                                        }
                                        special_content = "SPECIAL:" + json.dumps(special_payload)
                                        
                                        # Save to DB
                                        if room_obj:
                                            db_msg = Message(content=special_content, user_id=None, room_id=room_obj.id)
                                            db.session.add(db_msg)
                                            db.session.commit()

                                        # Broadcast
                                        broadcast(room, {
                                            'type': 'chat', # Send as chat so frontend appendMessage handles it (we will update appendMessage)
                                            'user': '小天气',
                                            'content': special_content,
                                            'timestamp': datetime.now().strftime('%H:%M')
                                        })

                                except Exception as e:
                                    print(f"Weather Error: {e}")
                                    broadcast(room, {
                                        'type': 'chat',
                                        'user': 'System',
                                        'content': f"天气查询出错: {str(e)}",
                                        'timestamp': datetime.now().strftime('%H:%M')
                                    })

                            # Check for Music Trigger
                            elif content.startswith('小音乐'):
                                try:
                                    cmd = content.strip()
                                    mode = None
                                    if '群内送歌' in cmd:
                                        mode = 'gift'
                                    elif '随机播放' in cmd:
                                        mode = 'random'
                                    
                                    if mode:
                                        broadcast(room, {
                                            'type': 'chat', 
                                            'user': '小音乐', 
                                            'content': "正在获取音乐...", 
                                            'timestamp': datetime.now().strftime('%H:%M')
                                        })

                                        data = get_music_data(mode)
                                        
                                        if 'error' in data:
                                            broadcast(room, {
                                                'type': 'chat',
                                                'user': '小音乐',
                                                'content': f"获取失败: {data['error']}",
                                                'timestamp': datetime.now().strftime('%H:%M')
                                            })
                                        else:
                                            # Construct Special Message
                                            special_type = 'music_gift' if mode == 'gift' else 'music_private'
                                            special_payload = {
                                                'type': special_type,
                                                'data': data,
                                                'target_user': user if mode == 'random' else None
                                            }
                                            special_content = "SPECIAL:" + json.dumps(special_payload)
                                            
                                            # Save to DB
                                            if room_obj:
                                                db_msg = Message(content=special_content, user_id=None, room_id=room_obj.id)
                                                db.session.add(db_msg)
                                                db.session.commit()
                                            
                                            # Broadcast
                                            broadcast(room, {
                                                'type': 'chat',
                                                'user': '小音乐',
                                                'content': special_content,
                                                'timestamp': datetime.now().strftime('%H:%M')
                                            })
                                            
                                except Exception as e:
                                    print(f"Music Error: {e}")
                                    broadcast(room, {
                                        'type': 'chat',
                                        'user': 'System',
                                        'content': f"音乐服务出错: {str(e)}",
                                        'timestamp': datetime.now().strftime('%H:%M')
                                    })

    except Exception as e:
        print(f"WS Error: {e}")
        db.session.remove() # Ensure release on error
    finally:
        # Log Leave/Logout
        if user:
            try:
                if room:
                    log_leave = ActivityLog(user_id=user_obj.id if user_obj else None, username=user, action='leave_room', content=room)
                    db.session.add(log_leave)
                log_out = ActivityLog(user_id=user_obj.id if user_obj else None, username=user, action='logout', content='下线')
                db.session.add(log_out)
                db.session.commit()
            except:
                db.session.rollback()

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
