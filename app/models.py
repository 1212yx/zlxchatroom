from .extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    nickname = db.Column(db.String(64))  # Added nickname field
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_banned = db.Column(db.Boolean, default=False)  # 封禁状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# 房间成员关联表
room_members = db.Table('room_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('room_id', db.Integer, db.ForeignKey('rooms.id'), primary_key=True)
)

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned = db.Column(db.Boolean, default=False)
    
    # 创建人
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator = db.relationship('User', foreign_keys=[creator_id], backref=db.backref('created_rooms', lazy='dynamic'))

    # 关系
    members = db.relationship('User', secondary=room_members, lazy='dynamic',
        backref=db.backref('rooms', lazy='dynamic'))
    messages = db.relationship('Message', backref='room', lazy='dynamic')

class WSServer(db.Model):
    __tablename__ = 'ws_servers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    address = db.Column(db.String(128)) # ws://ip:port
    description = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Room {self.name}>'

# 管理员-角色关联表
admin_roles = db.Table('admin_roles',
    db.Column('admin_id', db.Integer, db.ForeignKey('admin_users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    nickname = db.Column(db.String(64))
    avatar = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    is_super = db.Column(db.Boolean, default=False) # 超级管理员标识
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 角色关联
    roles = db.relationship('Role', secondary=admin_roles,
                          backref=db.backref('admins', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<AdminUser {self.username}>'

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    
    # 建立关系
    author = db.relationship('User', backref=db.backref('messages', lazy='dynamic'))

    def __repr__(self):
        return f'<Message {self.id}>'

class AIModel(db.Model):
    __tablename__ = 'ai_models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    api_url = db.Column(db.String(256), nullable=False)
    api_key = db.Column(db.String(256), nullable=False)
    model_name = db.Column(db.String(128), nullable=False)
    prompt = db.Column(db.Text, nullable=True)
    token_usage = db.Column(db.Integer, default=0)
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AIModel {self.name}>'

class ThirdPartyApi(db.Model):
    __tablename__ = 'third_party_apis'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    command = db.Column(db.String(32), unique=True, nullable=False) # e.g. @weather
    url = db.Column(db.String(256), nullable=False)
    token = db.Column(db.String(256), nullable=True)
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ThirdPartyApi {self.name}>'

# 角色-菜单关联表
role_menus = db.Table('role_menus',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('menu_id', db.Integer, db.ForeignKey('menus.id'), primary_key=True)
)

class Menu(db.Model):
    __tablename__ = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    icon = db.Column(db.String(64), default='layui-icon-circle')
    url = db.Column(db.String(128)) # route endpoint or url
    parent_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=True)
    order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    
    # Relationship for nested menus
    children = db.relationship('Menu', 
                             backref=db.backref('parent', remote_side=[id]),
                             order_by='Menu.order')

    def __repr__(self):
        return f'<Menu {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'url': self.url,
            'parent_id': self.parent_id,
            'order': self.order,
            'is_visible': self.is_visible
        }

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    
    # Relationship with menus
    menus = db.relationship('Menu', secondary=role_menus, 
                          backref=db.backref('roles', lazy='dynamic'))

    def __repr__(self):
        return f'<Role {self.name}>'

class AIChatSession(db.Model):
    __tablename__ = 'ai_chat_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    ai_model_id = db.Column(db.Integer, db.ForeignKey('ai_models.id'), nullable=True)
    title = db.Column(db.String(256), default="New Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    messages = db.relationship('AIChatMessage', backref='session', lazy='dynamic', cascade="all, delete-orphan")
    user = db.relationship('AdminUser', backref='ai_sessions')
    ai_model = db.relationship('AIModel', backref='sessions')

    def __repr__(self):
        return f'<AIChatSession {self.title}>'

class AIChatMessage(db.Model):
    __tablename__ = 'ai_chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('ai_chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False) # user, ai, system
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AIChatMessage {self.id}>'

# Sensitive Word Module
class SensitiveWord(db.Model):
    __tablename__ = 'sensitive_words'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'))

    def __repr__(self):
        return f'<SensitiveWord {self.word}>'

class WarningLog(db.Model):
    __tablename__ = 'warning_logs'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(512))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) # Normal user
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    triggered_word = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('warnings', lazy='dynamic'))
    room = db.relationship('Room', backref=db.backref('warnings', lazy='dynamic'))

    def __repr__(self):
        return f'<WarningLog {self.id}>'

class RoomFile(db.Model):
    __tablename__ = 'room_files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False) # 存储的文件名
    original_filename = db.Column(db.String(256), nullable=False) # 原始文件名
    file_size = db.Column(db.Integer, default=0) # 文件大小，单位字节
    file_type = db.Column(db.String(64)) # 文件类型/扩展名
    file_path = db.Column(db.String(512)) # 文件存储路径
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('files', lazy='dynamic'))
    room = db.relationship('Room', backref=db.backref('files', lazy='dynamic'))

    def __repr__(self):
        return f'<RoomFile {self.original_filename}>'

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(64)) 
    action = db.Column(db.String(32)) # login, logout, join_room, leave_room, chat
    content = db.Column(db.String(256)) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<ActivityLog {self.action} - {self.username}>'
