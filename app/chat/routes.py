from flask import render_template, request, session, redirect, url_for, jsonify
from . import chat
from app.extensions import sock, db
from app.models import User, Room, Message, WSServer
from sqlalchemy import text, db
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
from app.bot.core import get_bot_response
from app.chat.weather import get_weather_data, parse_weather_video
from app.chat.music import get_music_data
from app.chat.news import get_news_data

# In-memory store for connected clients: {room_id: set(ws)}
# Using set for O(1) removal, but ws objects need to be hashable. They usually are.
rooms = {}
# Mapping from ws object to username for tracking who is who
ws_user_map = {}
# Mapping from ws object to username for tracking who is who
ws_user_map = {}

@chat.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username') # Using 'username' field from login form
        username = request.form.get('username') # Using 'username' field from login form
        password = request.form.get('password')
        server = request.form.get('server')
        
        if username and password and server:
            user = User.query.filter_by(username=username).first()
            
            if not user:
            user = User.query.filter_by(username=username).first()
            
            if not user:
                error = "该账号未注册，请先注册账号"
            elif not user.check_password(password):
            elif not user.check_password(password):
                error = "账号或密码错误"
            else:
                session['user'] = user.nickname # Store nickname in session for display
                session['username'] = user.username # Store username in session for identification
                session['user'] = user.nickname # Store nickname in session for display
                session['username'] = user.username # Store username in session for identification
                session['server'] = server
                return redirect(url_for('chat.home'))
            
    # 获取所有激活的服务器
    servers = WSServer.query.filter_by(is_active=True).all()
    return render_template('chat/login.html', error=error, servers=servers)
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

@chat.route('/api/music/random')
def api_music_random():
    data = get_music_data('random')
    return json.dumps(data)

@sock.route('/ws', bp=chat)
def websocket(ws):
    print("DEBUG: Websocket function called - Version 3")
    username = session.get('username')
    user_obj = User.query.filter_by(username=username).first() if username else None
    
    user = None
    room = None
    room_obj = None
    
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
                         
                         ws.send(json.dumps({
                            'type': 'chat',
                            'user': sender_name,
                            'content': h_msg.content,
                            'timestamp': h_msg.timestamp.strftime('%H:%M'),
                            'is_history': True
                         }))
                
                # Broadcast join
                print("Broadcasting join...")
                broadcast(room, {
                    'type': 'system', 
                    'content': f'{user} 加入了 {room}',
                    'timestamp': datetime.now().strftime('%H:%M')
                })
                
                # Broadcast updated user list
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
                            # Save User Message to DB
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
                                    # Support various formats: "小天气 北京", "小天气:北京", "小天气：北京"
                                    # Remove "小天气" prefix
                                    raw_city = content[3:].strip()
                                    # Remove common separators
                                    city = raw_city.replace(':', '').replace('：', '').strip()
                                    
                                    if not city:
                                        city = "内江"
                                    
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
                                        # 1. Notify "Fetching..."
                                        if mode == 'random':
                                            ws.send(json.dumps({
                                                'type': 'chat', 
                                                'user': '小音乐', 
                                                'content': "正在获取音乐...", 
                                                'timestamp': datetime.now().strftime('%H:%M')
                                            }))
                                        else:
                                            broadcast(room, {
                                                'type': 'chat', 
                                                'user': '小音乐', 
                                                'content': "正在获取音乐...", 
                                                'timestamp': datetime.now().strftime('%H:%M')
                                            })

                                        data = get_music_data(mode)
                                        
                                        if 'error' in data:
                                            error_msg = f"获取失败: {data['error']}"
                                            if mode == 'random':
                                                ws.send(json.dumps({
                                                    'type': 'chat',
                                                    'user': '小音乐',
                                                    'content': error_msg,
                                                    'timestamp': datetime.now().strftime('%H:%M')
                                                }))
                                            else:
                                                broadcast(room, {
                                                    'type': 'chat',
                                                    'user': '小音乐',
                                                    'content': error_msg,
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
                                            
                                            if mode == 'random':
                                                # Private: Send only to requester, don't save to DB
                                                ws.send(json.dumps({
                                                    'type': 'chat',
                                                    'user': '小音乐',
                                                    'content': special_content,
                                                    'timestamp': datetime.now().strftime('%H:%M')
                                                }))
                                            else:
                                                # Public (Gift): Save to DB and Broadcast
                                                if room_obj:
                                                    db_msg = Message(content=special_content, user_id=None, room_id=room_obj.id)
                                                    db.session.add(db_msg)
                                                    db.session.commit()
                                                
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

                            # Check for News Trigger
                            elif content.strip() == '小新闻':
                                try:
                                    broadcast(room, {
                                        'type': 'chat', 
                                        'user': '小新闻', 
                                        'content': "正在获取新闻...", 
                                        'timestamp': datetime.now().strftime('%H:%M')
                                    })

                                    data = get_news_data()
                                    
                                    if 'error' in data:
                                        broadcast(room, {
                                            'type': 'chat',
                                            'user': '小新闻',
                                            'content': f"获取失败: {data['error']}",
                                            'timestamp': datetime.now().strftime('%H:%M')
                                        })
                                    else:
                                        # Construct Special Message
                                        special_payload = {
                                            'type': 'news_card',
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
                                            'type': 'chat',
                                            'user': '小新闻',
                                            'content': special_content,
                                            'timestamp': datetime.now().strftime('%H:%M')
                                        })
                                        
                                except Exception as e:
                                    print(f"News Error: {e}")
                                    broadcast(room, {
                                        'type': 'chat',
                                        'user': 'System',
                                        'content': f"新闻服务出错: {str(e)}",
                                        'timestamp': datetime.now().strftime('%H:%M')
                                    })

                            # Check for Video Trigger
                            elif content.strip().startswith('小视频'):
                                try:
                                    # Normalize content
                                    raw_content = content.strip().replace('　', ' ')
                                    
                                    video_url = None
                                    # Flexible parsing strategies
                                    if ' ' in raw_content:
                                        # Split by first space
                                        parts = raw_content.split(' ', 1)
                                        if len(parts) > 1 and parts[1].strip():
                                            video_url = parts[1].strip()
                                    
                                    if not video_url and ('：' in raw_content or ':' in raw_content):
                                        # Split by colon
                                        clean_content = raw_content.replace('：', ':')
                                        parts = clean_content.split(':', 1)
                                        if len(parts) > 1 and parts[1].strip():
                                            video_url = parts[1].strip()
                                            
                                    if not video_url:
                                        # Try to find http/https directly
                                        http_idx = raw_content.find('http')
                                        if http_idx > 0:
                                            video_url = raw_content[http_idx:].strip()

                                    if video_url:
                                        # Broadcast processing message
                                        broadcast(room, {
                                            'type': 'chat',
                                            'user': 'System',
                                            'content': f"正在解析视频: {video_url}",
                                            'timestamp': datetime.now().strftime('%H:%M')
                                        })

                                        # Get Parsing API
                                        try:
                                            # Using raw SQL to bypass any model import issues causing NameError
                                            sql = text("SELECT url FROM third_party_apis WHERE command = :cmd AND is_enabled = 1 LIMIT 1")
                                            result = db.session.execute(sql, {'cmd': '小视频 url'}).fetchone()
                                            
                                            if result:
                                                class SimpleConfig:
                                                    pass
                                                api_config = SimpleConfig()
                                                api_config.url = result[0]
                                            else:
                                                api_config = None
                                                
                                        except Exception as e:
                                            print(f"CRITICAL ERROR in Video API lookup: {e}")
                                            import traceback
                                            traceback.print_exc()
                                            api_config = None
                                        
                                        if api_config:
                                            parsing_url = api_config.url
                                            iframe_src = f"{parsing_url}{video_url}"
                                            
                                            special_payload = {
                                                'type': 'video_embed',
                                                'data': {
                                                    'src': iframe_src,
                                                    'original_url': video_url
                                                }
                                            }
                                            special_content = "SPECIAL:" + json.dumps(special_payload)
                                            
                                            # Save to DB
                                            if room_obj:
                                                db_msg = Message(content=special_content, user_id=None, room_id=room_obj.id)
                                                db.session.add(db_msg)
                                                db.session.commit()
                                            
                                            broadcast(room, {
                                                'type': 'chat',
                                                'user': '小视频',
                                                'content': special_content,
                                                'timestamp': datetime.now().strftime('%H:%M')
                                            })
                                        else:
                                            broadcast(room, {
                                                'type': 'chat',
                                                'user': 'System',
                                                'content': "未配置小视频解析接口，请联系管理员。",
                                                'timestamp': datetime.now().strftime('%H:%M')
                                            })
                                    else:
                                        # Only warn if it looks like a failed attempt (e.g. just "小视频")
                                        if raw_content == '小视频':
                                            broadcast(room, {
                                                'type': 'chat',
                                                'user': 'System',
                                                'content': "正在为您随机推荐精彩视频...",
                                                'timestamp': datetime.now().strftime('%H:%M')
                                            })
                                            
                                            try:
                                                import requests
                                                import random
                                                
                                                video_url = None
                                                
                                                # List of APIs to try
                                                # Note: Public APIs are often unstable, so we have multiple backups
                                                apis = [
                                                    "https://api.uomg.com/api/rand.douyin?format=json",
                                                    "https://api.yujn.cn/api/zzxjj.php?type=json",
                                                    "https://api.btstu.cn/sjbz/api.php?method=mobile&format=json"
                                                ]
                                                
                                                # 1. Try APIs
                                                for api in apis:
                                                    try:
                                                        print(f"DEBUG: Trying Video API: {api}")
                                                        resp = requests.get(api, timeout=5)
                                                        if resp.status_code == 200:
                                                            data = resp.json()
                                                            # Different APIs have different response structures
                                                            if 'video_url' in data:
                                                                video_url = data['video_url']
                                                            elif 'data' in data and isinstance(data['data'], str) and data['data'].startswith('http'):
                                                                video_url = data['data']
                                                            elif 'url' in data: # Common pattern
                                                                video_url = data['url']
                                                                
                                                            if video_url and video_url.startswith('http'):
                                                                print(f"DEBUG: Found video url: {video_url}")
                                                                break # Success!
                                                    except Exception as e:
                                                        print(f"API {api} failed: {e}")
                                                        continue
                                                
                                                # 2. Fallback to hardcoded safe videos if all APIs fail
                                                if not video_url:
                                                    print("DEBUG: All APIs failed, using fallback video.")
                                                    fallback_videos = [
                                                        "https://v.api.aa1.cn/api/api-dy/video/01.mp4", # Example public API that returns video directly (might redirect)
                                                        # Using some known static video URLs (replace with reliable ones if available)
                                                        "https://www.w3schools.com/html/mov_bbb.mp4", # Reliable test video
                                                        "https://media.w3.org/2010/05/sintel/trailer.mp4"
                                                    ]
                                                    video_url = random.choice(fallback_videos)

                                                if video_url:
                                                    special_payload = {
                                                        'type': 'video_embed',
                                                        'data': {
                                                            'src': video_url,
                                                            'original_url': video_url
                                                        }
                                                    }
                                                    special_content = "SPECIAL:" + json.dumps(special_payload)
                                                    
                                                    if room_obj:
                                                        db_msg = Message(content=special_content, user_id=None, room_id=room_obj.id)
                                                        db.session.add(db_msg)
                                                        db.session.commit()
                                                    
                                                    broadcast(room, {
                                                        'type': 'chat',
                                                        'user': '小视频',
                                                        'content': special_content,
                                                        'timestamp': datetime.now().strftime('%H:%M')
                                                    })
                                                else:
                                                    broadcast(room, {
                                                        'type': 'chat',
                                                        'user': 'System',
                                                        'content': "未能获取到随机视频，请重试。",
                                                        'timestamp': datetime.now().strftime('%H:%M')
                                                    })
                                                    
                                            except Exception as e:
                                                print(f"Random Video Error: {e}")
                                                broadcast(room, {
                                                    'type': 'chat',
                                                    'user': 'System',
                                                    'content': "获取随机视频失败，请稍后重试。",
                                                    'timestamp': datetime.now().strftime('%H:%M')
                                                })
                                except Exception as e:
                                    print(f"Video Error: {e}")
                                    broadcast(room, {
                                        'type': 'chat',
                                        'user': 'System',
                                        'content': f"视频服务出错: {str(e)}",
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
