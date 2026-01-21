from flask import render_template, request, redirect, url_for, flash, session, current_app, jsonify
from . import admin
from ..models import AdminUser, User, Room, WSServer, AIModel, ThirdPartyApi
from ..extensions import db
from functools import wraps
import os
import time
from werkzeug.utils import secure_filename
import openai

# 管理员登录验证装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user_id' not in session:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@admin_required
def index():
    user_count = User.query.count()
    room_count = Room.query.count()
    server_count = WSServer.query.count()
    # Assuming layout handles menu rendering
    return render_template('admin/index.html', user_count=user_count, room_count=room_count, server_count=server_count)

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['admin_user_id'] = user.id
            return redirect(url_for('admin.index'))
        flash('用户名或密码错误', 'danger')
    return render_template('admin/login.html')

@admin.route('/logout')
def logout():
    session.pop('admin_user_id', None)
    return redirect(url_for('admin.login'))

@admin.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.paginate(page=page, per_page=12, error_out=False)
    users = pagination.items
    return render_template('admin/user_list.html', users=users, pagination=pagination)

@admin.route('/users/<int:id>/ban', methods=['POST'])
@admin_required
def ban_user(id):
    user = User.query.get_or_404(id)
    user.is_banned = not user.is_banned
    db.session.commit()
    return {'status': 'success', 'message': '操作成功'}

@admin.route('/users/<int:id>/delete', methods=['POST'])
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return {'status': 'success', 'message': '用户已删除'}

@admin.route('/servers')
@admin_required
def servers():
    page = request.args.get('page', 1, type=int)
    pagination = WSServer.query.paginate(page=page, per_page=12, error_out=False)
    servers = pagination.items
    return render_template('admin/servers.html', servers=servers, pagination=pagination)

@admin.route('/servers/add', methods=['POST'])
@admin_required
def add_server():
    name = request.form.get('name')
    address = request.form.get('address')
    description = request.form.get('description')
    
    if WSServer.query.filter_by(name=name).first():
        return {'status': 'error', 'message': '服务器名称已存在'}
    
    server = WSServer(name=name, address=address, description=description)
    db.session.add(server)
    db.session.commit()
    return {'status': 'success', 'message': '添加成功'}

@admin.route('/servers/<int:id>', methods=['GET'])
@admin_required
def get_server(id):
    server = WSServer.query.get_or_404(id)
    return {
        'id': server.id,
        'name': server.name,
        'address': server.address,
        'description': server.description,
        'is_active': server.is_active,
        'created_at': server.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }

@admin.route('/servers/<int:id>/edit', methods=['POST'])
@admin_required
def edit_server(id):
    server = WSServer.query.get_or_404(id)
    server.name = request.form.get('name')
    server.address = request.form.get('address')
    server.description = request.form.get('description')
    db.session.commit()
    return {'status': 'success', 'message': '修改成功'}

@admin.route('/servers/<int:id>/delete', methods=['POST'])
@admin_required
def delete_server(id):
    server = WSServer.query.get_or_404(id)
    db.session.delete(server)
    db.session.commit()
    return {'status': 'success', 'message': '删除成功'}

@admin.route('/servers/<int:id>/toggle', methods=['POST'])
@admin_required
def toggle_server(id):
    server = WSServer.query.get_or_404(id)
    server.is_active = not server.is_active
    db.session.commit()
    return {'status': 'success', 'message': '状态更新成功'}

@admin.route('/rooms')
@admin_required
def rooms():
    page = request.args.get('page', 1, type=int)
    pagination = Room.query.paginate(page=page, per_page=12, error_out=False)
    rooms = pagination.items
    return render_template('admin/rooms.html', rooms=rooms, pagination=pagination)

@admin.route('/rooms/<int:room_id>/members')
@admin_required
def room_members(room_id):
    room = Room.query.get_or_404(room_id)
    members = []
    for m in room.members:
        members.append({
            'id': m.id,
            'username': m.username,
            'is_banned': m.is_banned
        })
    return {'data': members}

@admin.route('/rooms/<int:id>/delete', methods=['POST'])
@admin_required
def delete_room(id):
    room = Room.query.get_or_404(id)
    db.session.delete(room)
    db.session.commit()
    return {'status': 'success', 'message': '删除成功'}

@admin.route('/rooms/<int:id>/ban', methods=['POST'])
@admin_required
def ban_room(id):
    room = Room.query.get_or_404(id)
    room.is_banned = not room.is_banned
    db.session.commit()
    return {'status': 'success', 'message': '操作成功'}

@admin.route('/rooms/<int:id>', methods=['GET'])
@admin_required
def get_room(id):
    room = Room.query.get_or_404(id)
    return {
        'id': room.id,
        'name': room.name,
        'description': room.description,
        'creator': room.creator.username if room.creator else 'Unknown',
        'created_at': room.created_at.strftime('%Y-%m-%d'),
        'member_count': room.members.count()
    }

@admin.route('/profile', methods=['GET', 'POST'])
@admin_required
def profile():
    user = AdminUser.query.get(session['admin_user_id'])
    if request.method == 'POST':
        nickname = request.form.get('nickname')
        user.nickname = nickname
        
        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                # Ensure uploads directory exists
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'avatars')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                filename = secure_filename(f"admin_{user.id}_{int(time.time())}.png")
                try:
                    file.save(os.path.join(upload_folder, filename))
                    user.avatar = filename
                    print(f"File saved to {os.path.join(upload_folder, filename)}") # Debug print
                except Exception as e:
                    print(f"Error saving file: {e}")
                    flash('头像保存失败，请重试', 'danger')
            else:
                flash('不支持的文件格式', 'warning')
            
        db.session.commit()
        flash('基本资料已更新', 'success')
        return redirect(url_for('admin.profile'))
        
    return render_template('admin/profile.html', user=user)

@admin.route('/security', methods=['GET', 'POST'])
@admin_required
def security():
    user = AdminUser.query.get(session['admin_user_id'])
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not user.check_password(current_password):
            flash('当前密码错误', 'danger')
        elif new_password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
        else:
            user.set_password(new_password)
            db.session.commit()
            flash('密码修改成功，请重新登录', 'success')
            return redirect(url_for('admin.logout'))
            
    return render_template('admin/security.html')

# ================= AI Model Engine Routes =================

@admin.route('/ai-models')
@admin_required
def ai_models():
    page = request.args.get('page', 1, type=int)
    per_page = 6
    pagination = AIModel.query.order_by(AIModel.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    models = pagination.items
    return render_template('admin/ai_models.html', models=models, pagination=pagination)

@admin.route('/ai-models/add', methods=['POST'])
@admin_required
def ai_model_add():
    name = request.form.get('name')
    api_url = request.form.get('api_url')
    api_key = request.form.get('api_key')
    model_name = request.form.get('model_name')
    prompt = request.form.get('prompt')
    
    if not all([name, api_url, api_key, model_name]):
        flash('请填写完整信息', 'danger')
        return redirect(url_for('admin.ai_models'))
        
    model = AIModel(
        name=name,
        api_url=api_url,
        api_key=api_key,
        model_name=model_name,
        prompt=prompt
    )
    db.session.add(model)
    db.session.commit()
    flash('模型添加成功', 'success')
    return redirect(url_for('admin.ai_models'))

@admin.route('/ai-models/edit/<int:id>', methods=['POST'])
@admin_required
def ai_model_edit(id):
    model = AIModel.query.get_or_404(id)
    model.name = request.form.get('name')
    model.api_url = request.form.get('api_url')
    model.api_key = request.form.get('api_key')
    model.model_name = request.form.get('model_name')
    model.prompt = request.form.get('prompt')
    
    db.session.commit()
    flash('模型更新成功', 'success')
    return redirect(url_for('admin.ai_models'))

@admin.route('/ai-models/delete/<int:id>')
@admin_required
def ai_model_delete(id):
    model = AIModel.query.get_or_404(id)
    db.session.delete(model)
    db.session.commit()
    flash('模型已删除', 'success')
    return redirect(url_for('admin.ai_models'))

@admin.route('/ai-models/toggle/<int:id>')
@admin_required
def ai_model_toggle(id):
    model = AIModel.query.get_or_404(id)
    model.is_enabled = not model.is_enabled
    db.session.commit()
    status = '启用' if model.is_enabled else '禁用'
    flash(f'模型已{status}', 'success')
    return redirect(url_for('admin.ai_models'))

@admin.route('/ai-models/test', methods=['POST'])
@admin_required
def ai_model_test():
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    model_name = data.get('model_name')
    message = data.get('message')
    history = data.get('history', [])
    system_prompt = data.get('prompt', '')

    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url=api_url
        )
        
        messages = []
        # Add system prompt with Chinese instruction
        if system_prompt:
            # Append strong instruction to user provided prompt
            system_prompt += "\\n\\nIMPORTANT: You must output in Chinese language only. 无论用户使用什么语言，请始终用中文回答。"
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": "You are a helpful assistant. Please answer in Chinese. 你是一个乐于助人的助手，请始终用中文回答所有问题。"})
            
        # Add history
        if history:
            messages.extend(history)
            
        # Add current message if provided separately
        if message:
            messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=2048,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        return jsonify({'success': True, 'reply': reply})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ================= AI Robot List Routes =================

@admin.route('/robots')
@admin_required
def robots():
    robots_list = [
        {
            'name': '小师妹',
            'command': '@小师妹',
            'description': '智能对话机器人，支持自然语言交互',
            'example': '@小师妹 你好'
        },
        {
            'name': '小天气',
            'command': '小天气',
            'description': '查询当前所在地天气信息，支持自动生成天气卡片和背景视频',
            'example': '小天气'
        },
        {
            'name': '小天气 city',
            'command': '小天气 [城市名]',
            'description': '查询指定城市的天气信息',
            'example': '小天气 北京'
        },
        {
            'name': '小新闻',
            'command': '小新闻',
            'description': '获取最新的即时新闻资讯',
            'example': '小新闻'
        },
        {
            'name': '小视频',
            'command': '小视频',
            'description': '随机推荐并播放精彩短视频',
            'example': '小视频'
        },
        {
            'name': '小视频 url',
            'command': '小视频 [链接]',
            'description': '解析并播放指定链接的视频（支持抖音、快手等平台链接）',
            'example': '小视频 https://v.douyin.com/...'
        },
        {
            'name': '小音乐 随机播放',
            'command': '小音乐 随机播放',
            'description': '随机播放一首热门歌曲',
            'example': '小音乐 随机播放'
        },
        {
            'name': '小音乐 群内送歌',
            'command': '小音乐 群内送歌 [歌名]',
            'description': '点播一首歌曲并分享给群内好友',
            'example': '小音乐 群内送歌 晴天'
        }
    ]
    return render_template('admin/robots.html', robots=robots_list)

# ================= Interface Management Routes =================

@admin.route('/apis')
@admin_required
def apis():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = ThirdPartyApi.query.order_by(ThirdPartyApi.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    apis = pagination.items
    return render_template('admin/apis.html', apis=apis, pagination=pagination)

@admin.route('/apis/add', methods=['POST'])
@admin_required
def api_add():
    name = request.form.get('name')
    command = request.form.get('command')
    url = request.form.get('url')
    token = request.form.get('token')
    
    if not all([name, command, url]):
        return {'status': 'error', 'message': '请填写完整信息'}
        
    if ThirdPartyApi.query.filter_by(command=command).first():
        return {'status': 'error', 'message': '指令已存在'}
        
    api = ThirdPartyApi(
        name=name,
        command=command,
        url=url,
        token=token
    )
    db.session.add(api)
    db.session.commit()
    return {'status': 'success', 'message': '接口添加成功'}

@admin.route('/apis/<int:id>/edit', methods=['POST'])
@admin_required
def api_edit(id):
    api = ThirdPartyApi.query.get_or_404(id)
    name = request.form.get('name')
    command = request.form.get('command')
    url = request.form.get('url')
    token = request.form.get('token')

    # Check if command exists for other APIs
    existing = ThirdPartyApi.query.filter_by(command=command).first()
    if existing and existing.id != id:
        return {'status': 'error', 'message': '指令已存在'}

    api.name = name
    api.command = command
    api.url = url
    api.token = token
    
    db.session.commit()
    return {'status': 'success', 'message': '接口更新成功'}

@admin.route('/apis/<int:id>/delete', methods=['POST'])
@admin_required
def api_delete(id):
    api = ThirdPartyApi.query.get_or_404(id)
    db.session.delete(api)
    db.session.commit()
    return {'status': 'success', 'message': '接口已删除'}

@admin.route('/apis/<int:id>/toggle', methods=['POST'])
@admin_required
def api_toggle(id):
    api = ThirdPartyApi.query.get_or_404(id)
    api.is_enabled = not api.is_enabled
    db.session.commit()
    return {'status': 'success', 'message': '状态更新成功'}

@admin.route('/apis/<int:id>', methods=['GET'])
@admin_required
def get_api(id):
    api = ThirdPartyApi.query.get_or_404(id)
    return {
        'id': api.id,
        'name': api.name,
        'command': api.command,
        'url': api.url,
        'token': api.token,
        'is_enabled': api.is_enabled
    }
