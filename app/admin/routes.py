from flask import render_template, request, redirect, url_for, flash, session, current_app, jsonify, Response, stream_with_context
from . import admin
from ..models import AdminUser, User, Room, WSServer, AIModel, ThirdPartyApi, Menu, Role, AIChatSession, AIChatMessage, Message, SensitiveWord, WarningLog, ActivityLog
from ..extensions import db
from ..services.ai_analysis import AIAnalysisService

from functools import wraps
import os
import time
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import openai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io


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

@admin.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin.route('/api/dashboard/stats')
@admin_required
def dashboard_stats():
    # Basic Stats
    user_count = User.query.count()
    room_count = Room.query.count()
    message_count = Message.query.count()
    
    # Active Rooms (rooms with recent messages or members)
    # For now, just return top 5 rooms by message count
    active_rooms = []
    rooms = Room.query.all()
    for room in rooms:
        # Use explicit query to avoid potential relationship loading issues
        msg_count = Message.query.filter_by(room_id=room.id).count()
        # member_count relies on the many-to-many relationship which should be stable
        member_count = room.members.count() if hasattr(room.members, 'count') else 0
        active_rooms.append({
            'name': room.name,
            'msg_count': msg_count,
            'member_count': member_count,
            'status': '活跃' if msg_count > 0 else '空闲'
        })
    active_rooms.sort(key=lambda x: x['msg_count'], reverse=True)
    active_rooms = active_rooms[:6]
    
    # Mock Sentiment Data for Top Active Rooms
    # In a real app, this would be aggregated from AI analysis of messages
    import random
    room_names = []
    sentiment_positive = []
    sentiment_neutral = []
    sentiment_negative = []
    
    for room in active_rooms:
        room_names.append(room['name'])
        # Generate random distribution that sums to 100%
        # Bias towards neutral/positive usually
        pos = random.randint(20, 60)
        neu = random.randint(30, 70)
        neg = random.randint(0, 20)
        
        # Normalize to 100
        total = pos + neu + neg
        sentiment_positive.append(round(pos / total * 100, 1))
        sentiment_neutral.append(round(neu / total * 100, 1))
        sentiment_negative.append(round(neg / total * 100, 1))
    
    sentiment_data = {
        'rooms': room_names,
        'positive': sentiment_positive,
        'neutral': sentiment_neutral,
        'negative': sentiment_negative
    }
    
    # Message Trends (Last 7 days)
    # Mock data for now or aggregate from DB (aggregating from DB might be slow without proper queries, but let's try)
    # Simpler: just last 7 days count
    dates = []
    msg_counts = []
    from datetime import timedelta
    today = datetime.now().date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        dates.append(day.strftime('%m-%d'))
        # Using string comparison for broader compatibility
        day_str = day.strftime('%Y-%m-%d')
        count = Message.query.filter(db.func.date(Message.timestamp) == day_str).count()
        msg_counts.append(count)
        
    # Warnings (Real data from WarningLog)
    warnings = []
    # Fetch recent warnings from WarningLog table
    recent_warnings = WarningLog.query.order_by(WarningLog.timestamp.desc()).limit(20).all()
    
    for w in recent_warnings:
        warnings.append({
            'time': w.timestamp.strftime('%H:%M:%S'),
            'user': w.user.username if w.user else 'Unknown',
            'content': f"发送被拦截: {w.triggered_word}",
            'room': w.room.name if w.room else 'Unknown'
        })
    
    # AI Summary (Rule-based for speed)
    ai_summary = "系统运行平稳。"
    if len(warnings) > 0:
        ai_summary = f"警告：检测到 {len(warnings)} 条潜在风险消息，请立即查看预警日志。"
    elif len(active_rooms) > 3:
        ai_summary = f"当前系统活跃，{len(active_rooms)} 个房间正在进行热烈讨论。建议关注服务器负载。"
    else:
        ai_summary = "当前系统处于空闲状态，各项指标正常。"

    return jsonify({
        'user_count': user_count,
        'room_count': room_count,
        'message_count': message_count,
        'active_rooms': active_rooms,
        'sentiment_data': sentiment_data,
        'dates': dates,
        'msg_counts': msg_counts,
        'warnings': warnings,
        'ai_summary': ai_summary
    })

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

# ================= Menu Management Routes =================

@admin.context_processor
def inject_menus():
    if 'admin_user_id' not in session:
        return {}
    
    current_admin = AdminUser.query.get(session['admin_user_id'])
    if not current_admin:
        return {}
        
    # If super admin, show all visible menus
    if current_admin.is_super:
        menus = Menu.query.filter_by(parent_id=None, is_visible=True).order_by(Menu.order).all()
        return {'admin_menus': menus, 'current_admin': current_admin}
    
    # Otherwise, filter by roles
    # Collect all accessible menu IDs
    accessible_menu_ids = set()
    for role in current_admin.roles:
        for menu in role.menus:
            accessible_menu_ids.add(menu.id)
            # Add children IDs too if parent is selected (optional, depends on logic)
            # Or usually, we select leaf nodes and parents should be inferred or explicitly selected.
            # Here we assume explicit selection.
            
    # Also need to ensure parents are visible if a child is visible
    # This might require recursive check or simpler approach:
    # Just fetch top level menus, and in template check if they or their children are in accessible_list
    
    # Better approach: Fetch all menus, filter in python
    all_top_menus = Menu.query.filter_by(parent_id=None, is_visible=True).order_by(Menu.order).all()
    final_menus = []
    
    for menu in all_top_menus:
        # Check if menu itself is accessible or has accessible children
        has_access = menu.id in accessible_menu_ids
        
        # Check children
        visible_children = []
        for child in menu.children:
            if child.id in accessible_menu_ids and child.is_visible:
                visible_children.append(child)
        
        # If parent has access or has visible children, include it
        if has_access or visible_children:
            # We need to temporarily attach filtered children to the menu object for rendering
            # But modifying SQLAlchemy object might be tricky if session is active.
            # Let's create a proxy structure or just attach a transient attribute
            menu.visible_children = visible_children
            final_menus.append(menu)
            
    return {'admin_menus': final_menus, 'current_admin': current_admin}

@admin.route('/menus')
@admin_required
def menus():
    # Fetch all menus to display in a tree-like structure or list
    menus = Menu.query.order_by(Menu.order).all()
    # Separate parents and children for easier rendering if needed, 
    # but the template can handle hierarchy if we pass all or structured data.
    # Here we just pass all and let the template or JS handle it, 
    # or we can pass top-level menus and let Jinja recursive loop.
    top_menus = Menu.query.filter_by(parent_id=None).order_by(Menu.order).all()
    return render_template('admin/menus.html', menus=top_menus)

@admin.route('/menus/add', methods=['POST'])
@admin_required
def menu_add():
    name = request.form.get('name')
    icon = request.form.get('icon')
    url = request.form.get('url')
    parent_id = request.form.get('parent_id')
    order = request.form.get('order', 0, type=int)
    is_visible = request.form.get('is_visible') == 'on'

    if not name:
        return {'status': 'error', 'message': '菜单名称不能为空'}

    if parent_id == '':
        parent_id = None
    
    menu = Menu(
        name=name,
        icon=icon,
        url=url,
        parent_id=parent_id,
        order=order,
        is_visible=is_visible
    )
    db.session.add(menu)
    db.session.commit()
    return {'status': 'success', 'message': '菜单添加成功'}

@admin.route('/menus/<int:id>', methods=['GET'])
@admin_required
def get_menu(id):
    menu = Menu.query.get_or_404(id)
    return {
        'id': menu.id,
        'name': menu.name,
        'icon': menu.icon,
        'url': menu.url,
        'parent_id': menu.parent_id,
        'order': menu.order,
        'is_visible': menu.is_visible
    }

@admin.route('/menus/<int:id>/edit', methods=['POST'])
@admin_required
def menu_edit(id):
    menu = Menu.query.get_or_404(id)
    menu.name = request.form.get('name')
    menu.icon = request.form.get('icon')
    menu.url = request.form.get('url')
    parent_id = request.form.get('parent_id')
    menu.order = request.form.get('order', 0, type=int)
    menu.is_visible = request.form.get('is_visible') == 'on'
    
    if parent_id == '' or parent_id == '0':
        menu.parent_id = None
    else:
        menu.parent_id = int(parent_id)
        
    db.session.commit()
    return {'status': 'success', 'message': '菜单更新成功'}

@admin.route('/menus/<int:id>/delete', methods=['POST'])
@admin_required
def menu_delete(id):
    menu = Menu.query.get_or_404(id)
    # Check if it has children
    if len(menu.children) > 0:
        return {'status': 'error', 'message': '请先删除子菜单'}
        
    db.session.delete(menu)
    db.session.commit()
    return {'status': 'success', 'message': '菜单已删除'}

# ================= Role Management Routes =================

@admin.route('/roles')
@admin_required
def roles():
    roles = Role.query.all()
    # Get all menus for permission assignment modal
    all_menus = Menu.query.order_by(Menu.order).all()
    return render_template('admin/roles.html', roles=roles, all_menus=all_menus)

@admin.route('/roles/add', methods=['POST'])
@admin_required
def role_add():
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        menu_ids = data.get('menu_ids', [])
    else:
        name = request.form.get('name')
        description = request.form.get('description')
        menu_ids = request.form.getlist('menu_ids[]')
    
    if not name:
        return {'status': 'error', 'message': '角色名称不能为空'}
        
    if Role.query.filter_by(name=name).first():
        return {'status': 'error', 'message': '角色名称已存在'}
        
    role = Role(name=name, description=description)
    
    if menu_ids:
        for mid in menu_ids:
            menu = Menu.query.get(mid)
            if menu:
                role.menus.append(menu)
                
    db.session.add(role)
    db.session.commit()
    return {'status': 'success', 'message': '角色添加成功'}

@admin.route('/roles/<int:id>', methods=['GET'])
@admin_required
def get_role(id):
    role = Role.query.get_or_404(id)
    # Get assigned menu IDs
    menu_ids = [m.id for m in role.menus]
    return {
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'menu_ids': menu_ids
    }

@admin.route('/roles/<int:id>/edit', methods=['POST'])
@admin_required
def role_edit(id):
    role = Role.query.get_or_404(id)
    role.name = request.form.get('name')
    role.description = request.form.get('description')
    
    # Update menu permissions
    menu_ids = request.form.getlist('menu_ids[]')
    # If using application/json
    if not menu_ids and request.json:
        menu_ids = request.json.get('menu_ids', [])
        
    # Clear existing menus and add new ones
    role.menus = []
    if menu_ids:
        for mid in menu_ids:
            menu = Menu.query.get(mid)
            if menu:
                role.menus.append(menu)
    
    db.session.commit()
    return {'status': 'success', 'message': '角色更新成功'}

@admin.route('/roles/<int:id>/delete', methods=['POST'])
@admin_required
def role_delete(id):
    role = Role.query.get_or_404(id)
    db.session.delete(role)
    db.session.commit()
    return {'status': 'success', 'message': '角色已删除'}

# ================= Admin User Management Routes =================

@admin.route('/admin-users')
@admin_required
def admin_list():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = AdminUser.query.order_by(AdminUser.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    admins = pagination.items
    
    # Get all roles for assignment modal
    roles = Role.query.all()
    
    return render_template('admin/admin_list.html', admins=admins, pagination=pagination, roles=roles)

@admin.route('/admin-users/add', methods=['POST'])
@admin_required
def admin_add():
    username = request.form.get('username')
    password = request.form.get('password')
    nickname = request.form.get('nickname')
    role_ids = request.form.getlist('role_ids[]')
    
    if not all([username, password]):
        return {'status': 'error', 'message': '用户名和密码不能为空'}
        
    if AdminUser.query.filter_by(username=username).first():
        return {'status': 'error', 'message': '用户名已存在'}
        
    admin = AdminUser(username=username, nickname=nickname)
    admin.set_password(password)
    
    if role_ids:
        for rid in role_ids:
            role = Role.query.get(rid)
            if role:
                admin.roles.append(role)
                
    db.session.add(admin)
    db.session.commit()
    return {'status': 'success', 'message': '管理员添加成功'}

@admin.route('/admin-users/<int:id>/edit', methods=['POST'])
@admin_required
def admin_edit(id):
    admin = AdminUser.query.get_or_404(id)
    
    # Basic info
    nickname = request.form.get('nickname')
    admin.nickname = nickname
    
    # Password update (optional)
    password = request.form.get('password')
    if password:
        admin.set_password(password)
        
    # Role update
    role_ids = request.form.getlist('role_ids[]')
    
    # Clear existing roles and add new ones
    admin.roles = []
    if role_ids:
        for rid in role_ids:
            role = Role.query.get(rid)
            if role:
                admin.roles.append(role)
                
    db.session.commit()
    return {'status': 'success', 'message': '管理员更新成功'}

@admin.route('/admin-users/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete(id):
    admin = AdminUser.query.get_or_404(id)
    
    if admin.username == 'admin':
        return {'status': 'error', 'message': '默认管理员账号不能删除'}
        
    db.session.delete(admin)
    db.session.commit()
    return {'status': 'success', 'message': '管理员已删除'}

@admin.route('/admin-users/<int:id>', methods=['GET'])
@admin_required
def get_admin(id):
    admin = AdminUser.query.get_or_404(id)
    role_ids = [r.id for r in admin.roles]
    return {
        'id': admin.id,
        'username': admin.username,
        'nickname': admin.nickname,
        'role_ids': role_ids
    }

# ================= AI Analysis Routes =================

@admin.route('/ai-analysis')
@admin_required
def ai_analysis():
    ai_models = AIModel.query.filter_by(is_enabled=True).all()
    print(f"DEBUG: ai_analysis route called. Found {len(ai_models)} models.")
    current_model = ai_models[0] if ai_models else None
    
    # Fetch sessions
    sessions = AIChatSession.query.filter_by(
        user_id=session['admin_user_id'], 
        is_deleted=False
    ).order_by(AIChatSession.updated_at.desc()).all()

    return render_template('admin/ai_analysis.html', 
                           ai_models=ai_models, 
                           current_model=current_model,
                           sessions=sessions)

@admin.route('/ai-analysis/sessions', methods=['POST'])
@admin_required
def create_session():
    data = request.json or {}
    title = data.get('title', 'New Chat')
    model_id = data.get('model_id')
    
    # If no model_id provided, use default
    if not model_id:
        model = AIModel.query.filter_by(is_enabled=True).first()
        model_id = model.id if model else None

    new_session = AIChatSession(
        user_id=session['admin_user_id'],
        title=title,
        ai_model_id=model_id
    )
    db.session.add(new_session)
    db.session.commit()
    
    return {'status': 'success', 'session': {
        'id': new_session.id,
        'title': new_session.title,
        'model_id': new_session.ai_model_id
    }}

@admin.route('/ai-analysis/sessions/<int:id>/messages', methods=['GET'])
@admin_required
def get_session_messages(id):
    chat_session = AIChatSession.query.get_or_404(id)
    if chat_session.user_id != session['admin_user_id']:
        return {'status': 'error', 'message': '未授权访问'}, 403
        
    messages = chat_session.messages.order_by(AIChatMessage.created_at).all()
    
    return {
        'status': 'success',
        'messages': [{
            'role': m.role,
            'content': m.content,
            'created_at': m.created_at.isoformat() if m.created_at else None
        } for m in messages]
    }

@admin.route('/ai-analysis/sessions/<int:id>', methods=['DELETE'])
@admin_required
def delete_session(id):
    chat_session = AIChatSession.query.get_or_404(id)
    if chat_session.user_id != session['admin_user_id']:
        return {'status': 'error', 'message': '未授权访问'}, 403
        
    chat_session.is_deleted = True
    db.session.commit()
    return {'status': 'success'}

@admin.route('/ai-analysis/chat', methods=['POST'])
@admin_required
def ai_analysis_chat():
    try:
        data = request.json
        message = data.get('message')
        history = data.get('history', [])
        model_id = data.get('model_id')
        session_id = data.get('session_id')
        
        print(f"DEBUG: Chat request - Session: {session_id}, Model: {model_id}, Msg: {message[:20]}")
        
        if not message:
            return jsonify({'error': '消息内容不能为空'}), 400
        
        messages = []
        
        if session_id:
            # Load session and history
            chat_session = AIChatSession.query.get(session_id)
            if chat_session and chat_session.user_id == session['admin_user_id']:
                # Save User Message
                user_msg = AIChatMessage(
                    session_id=session_id,
                    role='user',
                    content=message
                )
                db.session.add(user_msg)
                chat_session.updated_at = datetime.utcnow()
                db.session.commit()
                
                # Load history (last 20 messages for context)
                db_history = chat_session.messages.order_by(AIChatMessage.created_at.desc()).limit(20).all()
                # Reverse back to chronological order
                db_history_reversed = db_history[::-1]
                
                for m in db_history_reversed:
                    role = 'assistant' if m.role == 'ai' else m.role
                    messages.append({'role': role, 'content': m.content})
            else:
                if history:
                    messages.extend(history)
                messages.append({'role': 'user', 'content': message})
        else:
            # Create new session automatically
            chat_session = AIChatSession(
                user_id=session['admin_user_id'],
                title=message[:20] + "..." if len(message) > 20 else message,
                ai_model_id=model_id
            )
            db.session.add(chat_session)
            db.session.commit()
            session_id = chat_session.id
            
            # Save user message
            user_msg = AIChatMessage(
                session_id=session_id,
                role='user',
                content=message
            )
            db.session.add(user_msg)
            db.session.commit()
            
            messages.append({'role': 'user', 'content': message})
        
        service = AIAnalysisService(model_id)
        
        def generate():
            yield json.dumps({"type": "session_id", "content": session_id}) + "\n"
            yield from service.chat_stream(messages, session_id=session_id)

        return Response(stream_with_context(generate()), content_type='text/event-stream')
    except Exception as e:
        print(f"ERROR in ai_analysis_chat: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ================= Sensitive Word Routes =================

@admin.route('/sensitive-words')
@admin_required
def sensitive_words():
    words = SensitiveWord.query.order_by(SensitiveWord.created_at.desc()).all()
    return render_template('admin/sensitive_words.html', words=words)

@admin.route('/sensitive-words/add', methods=['POST'])
@admin_required
def add_sensitive_word():
    word = request.form.get('word')
    if word:
        existing = SensitiveWord.query.filter_by(word=word).first()
        if existing:
            return jsonify({'status': 'error', 'message': '敏感词已存在'})
        
        new_word = SensitiveWord(word=word, created_by=session.get('admin_user_id'))
        db.session.add(new_word)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': '敏感词不能为空'})

@admin.route('/api/dashboard/report')
@admin_required
def generate_dashboard_report():
    # 1. Gather Data
    user_count = User.query.count()
    room_count = Room.query.count()
    message_count = Message.query.count()
    
    # Active Rooms
    active_rooms = []
    rooms = Room.query.all()
    for room in rooms:
        msg_count = Message.query.filter_by(room_id=room.id).count()
        if msg_count > 0:
            active_rooms.append({'name': room.name, 'msg_count': msg_count, 'id': room.id})
    active_rooms.sort(key=lambda x: x['msg_count'], reverse=True)
    active_rooms = active_rooms[:5]
    
    # Mock Sentiment Data for Top Active Rooms
    # In a real app, this would be aggregated from AI analysis of messages
    import random
    room_names = []
    sentiment_positive = []
    sentiment_neutral = []
    sentiment_negative = []
    
    for room in active_rooms:
        room_names.append(room['name'])
        # Generate random distribution that sums to 100%
        # Bias towards neutral/positive usually
        pos = random.randint(20, 60)
        neu = random.randint(30, 70)
        neg = random.randint(0, 20)
        
        # Normalize to 100
        total = pos + neu + neg
        sentiment_positive.append(round(pos / total * 100, 1))
        sentiment_neutral.append(round(neu / total * 100, 1))
        sentiment_negative.append(round(neg / total * 100, 1))
    
    sentiment_data = {
        'rooms': room_names,
        'positive': sentiment_positive,
        'neutral': sentiment_neutral,
        'negative': sentiment_negative
    }
    
    # Recent Warnings
    recent_warnings = WarningLog.query.order_by(WarningLog.timestamp.desc()).limit(10).all()
    
    # 2. AI Summary
    ai_service = AIAnalysisService()
    
    prompt = f"""
    请根据以下系统数据生成一份简要的运营分析报告（中文）：
    - 总用户数: {user_count}
    - 总房间数: {room_count}
    - 总消息数: {message_count}
    - 活跃房间前5名: {', '.join([r['name'] for r in active_rooms])}
    - 最近预警数: {len(recent_warnings)}
    
    请包含以下部分：
    1. 整体概况
    2. 活跃度分析
    3. 安全风险提示
    """
    
    ai_summary = ""
    try:
        if ai_service.client:
            response = ai_service.client.chat.completions.create(
                model=ai_service.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            ai_summary = response.choices[0].message.content
        else:
            ai_summary = "AI模型未配置，无法生成智能分析。"
    except Exception as e:
        ai_summary = f"AI生成失败: {str(e)}"
        
    # 3. Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Register Chinese Font
    font_path = "C:\\Windows\\Fonts\\simhei.ttf"
    font_name = 'Helvetica' # Fallback
    try:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('SimHei', font_path))
            font_name = 'SimHei'
    except Exception as e:
        print(f"Font registration failed: {e}")
        
    styles = getSampleStyleSheet()
    # Create custom style for Chinese support
    styles.add(ParagraphStyle(name='ChineseNormal', parent=styles['Normal'], fontName=font_name, leading=14))
    styles.add(ParagraphStyle(name='ChineseHeading1', parent=styles['Heading1'], fontName=font_name, leading=20))
    styles.add(ParagraphStyle(name='ChineseHeading2', parent=styles['Heading2'], fontName=font_name, leading=16))
    
    story = []
    
    story.append(Paragraph("智联星队 - 可视化监控运营报告", styles['ChineseHeading1']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['ChineseNormal']))
    story.append(Spacer(1, 12))
    
    # Stats Table
    data = [
        ["指标", "数值"],
        ["总用户数", str(user_count)],
        ["总房间数", str(room_count)],
        ["总消息数", str(message_count)],
        ["活跃房间数", str(len(active_rooms))],
        ["最近预警数", str(len(recent_warnings))]
    ]
    
    t = Table(data, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t)
    story.append(Spacer(1, 24))
    
    # AI Analysis
    story.append(Paragraph("AI 智能分析", styles['ChineseHeading2']))
    story.append(Spacer(1, 12))
    
    # Handle newlines in AI summary
    for line in ai_summary.split('\n'):
        if line.strip():
            story.append(Paragraph(line, styles['ChineseNormal']))
            story.append(Spacer(1, 6))
            
    doc.build(story)
    buffer.seek(0)
    
    filename = f"AI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return Response(buffer, mimetype='application/pdf', 
                   headers={"Content-Disposition": f"attachment;filename={filename}"})

@admin.route('/sensitive-words/delete/<int:id>', methods=['POST'])
@admin_required
def delete_sensitive_word(id):
    word = SensitiveWord.query.get_or_404(id)
    db.session.delete(word)
    db.session.commit()
    return jsonify({'status': 'success'})

@admin.route('/api/monitor/search')
@admin_required
def monitor_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    
    results = []
    # Search Users
    users = User.query.filter(User.username.like(f'%{q}%')).limit(5).all()
    for u in users:
        results.append({'type': 'user', 'id': u.id, 'name': u.username, 'label': f'用户: {u.username}'})
        
    # Search Rooms
    rooms = Room.query.filter(Room.name.like(f'%{q}%')).limit(5).all()
    for r in rooms:
        results.append({'type': 'room', 'id': r.id, 'name': r.name, 'label': f'群组: {r.name}'})
        
    return jsonify(results)

@admin.route('/api/monitor/data')
@admin_required
def monitor_data():
    target_type = request.args.get('type')
    target_id = request.args.get('id')
    
    if not target_type or not target_id:
        return jsonify({'error': 'Missing params'}), 400
        
    data = {}
    import random
    from datetime import timedelta
    
    if target_type == 'user':
        user = User.query.get(target_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Mock Online Status
        last_msg = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).first()
        is_online = False
        if last_msg and (datetime.utcnow() - last_msg.timestamp) < timedelta(minutes=10):
            is_online = True
        
        # Recent Activity
        recent_msgs = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).limit(5).all()
        msg_list = [{'content': m.content, 'time': m.timestamp.strftime('%H:%M:%S'), 'room': m.room.name if m.room else 'Unknown'} for m in recent_msgs]
        
        # Active Rooms
        active_rooms = [r.name for r in user.rooms.limit(5).all()]
        
        data = {
            'name': user.username,
            'status': '在线' if is_online else '离线',
            'msg_count': Message.query.filter_by(user_id=user.id).count(),
            'recent_msgs': msg_list,
            'active_rooms': active_rooms,
            # Mock Social Score
            'social_score': random.randint(50, 95)
        }
        
    elif target_type == 'room':
        room = Room.query.get(target_id)
        if not room:
            return jsonify({'error': 'Room not found'}), 404
            
        # Stats
        total_members = room.members.count()
        online_members = random.randint(0, total_members) # Mock
        
        # Recent Chat Trend (Mock)
        trend = [random.randint(0, 10) for _ in range(10)]
        
        # Social Graph Nodes (Top 5 active users in room)
        active_users = db.session.query(User.username, db.func.count(Message.id)).join(Message).filter(Message.room_id == room.id).group_by(User.id).order_by(db.func.count(Message.id).desc()).limit(5).all()
        
        nodes = [{'name': u[0], 'value': u[1]} for u in active_users]
        links = []
        # Mock Links
        for i in range(len(nodes)):
            if i + 1 < len(nodes):
                links.append({'source': nodes[i]['name'], 'target': nodes[i+1]['name']})
        
        data = {
            'name': room.name,
            'total_members': total_members,
            'online_members': online_members,
            'trend': trend,
            'nodes': nodes,
            'links': links
        }
        
    return jsonify(data)

@admin.route('/api/monitor/activities')
@admin_required
def monitor_activities():
    # Fetch recent activities
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(50).all()
    
    data = []
    for log in logs:
        action_map = {
            'login': '上线',
            'logout': '下线',
            'join_room': '加入群聊',
            'leave_room': '离开群聊',
            'chat': '发送消息'
        }
        
        data.append({
            'time': log.timestamp.strftime('%H:%M:%S'),
            'username': log.username,
            'action': log.action,
            'content': log.content,
            'action_display': action_map.get(log.action, log.action)
        })
    
    return jsonify(data)
