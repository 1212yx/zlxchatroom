from flask import render_template, request, redirect, url_for, flash, session, current_app
from . import admin
from ..models import AdminUser, User
from ..extensions import db
from functools import wraps
import os
import time
from werkzeug.utils import secure_filename

# 管理员登录验证装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user_id' not in session:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['admin_user_id'] = user.id
            session['admin_username'] = user.username
            flash('登录成功', 'success')
            return redirect(url_for('admin.index'))
        else:
            flash('用户名或密码错误', 'danger')
            
    return render_template('admin/login.html')

@admin.route('/logout')
def logout():
    session.pop('admin_user_id', None)
    session.pop('admin_username', None)
    flash('已退出登录', 'info')
    return redirect(url_for('admin.login'))

from datetime import datetime, date

@admin.route('/')
@admin_required
def index():
    user_count = User.query.count()
    banned_count = User.query.filter_by(is_banned=True).count()
    admin_count = AdminUser.query.count()
    
    # 今日新增
    today_start = datetime.combine(date.today(), datetime.min.time())
    new_users_today = User.query.filter(User.created_at >= today_start).count()
    
    return render_template('admin/index.html', 
                           user_count=user_count, 
                           banned_count=banned_count, 
                           admin_count=admin_count,
                           new_users_today=new_users_today)

@admin.route('/users')
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.paginate(page=page, per_page=20, error_out=False)
    users = pagination.items
    return render_template('admin/user_list.html', users=users, pagination=pagination)

@admin.route('/users/<int:user_id>/toggle_ban', methods=['POST'])
@admin_required
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()
    status = '封禁' if user.is_banned else '解封'
    return {'status': 'success', 'message': f'用户已{status}', 'is_banned': user.is_banned}

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return {'status': 'success', 'message': '用户已删除'}

@admin.route('/init_admin')
def init_admin():
    # 临时路由，用于初始化管理员账号
    if not AdminUser.query.filter_by(username='admin').first():
        admin = AdminUser(username='admin')
        admin.set_password('admin888')
        db.session.add(admin)
        db.session.commit()
        return "管理员账号创建成功"
    return "管理员账号已存在"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin.route('/profile', methods=['GET', 'POST'])
@admin_required
def profile():
    user = AdminUser.query.get(session['admin_user_id'])
    if request.method == 'POST':
        nickname = request.form.get('nickname')
        if nickname:
            user.nickname = nickname
        
        file = request.files.get('avatar')
        print(f"DEBUG: request.files = {request.files}") # Debug
        print(f"DEBUG: form data = {request.form}") # Debug
        if file:
            print(f"DEBUG: filename = {file.filename}")
        
        if file and file.filename:
            if allowed_file(file.filename):
                # 获取文件后缀
                ext = file.filename.rsplit('.', 1)[1].lower()
                # 使用时间戳生成新文件名，避免中文乱码和重名
                filename = f"{int(time.time())}_{os.urandom(4).hex()}.{ext}"
                
                # Save path: app/admin/static/admin/avatars
                upload_folder = os.path.join(current_app.root_path, 'admin', 'static', 'admin', 'avatars')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
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
