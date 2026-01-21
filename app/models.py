from .extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# 好友关联表
friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    nickname = db.Column(db.String(64))  # Added nickname field
    nickname = db.Column(db.String(64))  # Added nickname field
    avatar = db.Column(db.String(256)) # Avatar URL or filename
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_banned = db.Column(db.Boolean, default=False)  # 封禁状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Friends relationship
    friends = db.relationship('User', 
        secondary=friendships,
        primaryjoin=(friendships.c.user_id == id),
        secondaryjoin=(friendships.c.friend_id == id),
        backref=db.backref('friend_of', lazy='dynamic'), 
        lazy='dynamic'
    )

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
    type = db.Column(db.String(20), default='group') # private, group
    
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
