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

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    nickname = db.Column(db.String(64))
    avatar = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

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

class Sticker(db.Model):
    __tablename__ = 'stickers'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(256), nullable=False)
    filename = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('stickers', lazy='dynamic'))

    def __repr__(self):
        return f'<Sticker {self.filename}>'

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

class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, accepted, rejected
    hello_message = db.Column(db.String(256)) # 验证信息
    remark = db.Column(db.String(64)) # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_friend_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_friend_requests')

class GroupRequest(db.Model):
    __tablename__ = 'group_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='group_requests')
    group = db.relationship('Room', backref='join_requests')
