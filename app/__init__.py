from flask import Flask
from config import config
from .extensions import db, socketio, migrate, sock

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    sock.init_app(app)

    # Import models to ensure they are registered with SQLAlchemy
    with app.app_context():
        from . import models

    # Register Blueprints
    from .chat import chat as chat_blueprint
    app.register_blueprint(chat_blueprint, url_prefix='/chat')

    from .bot import bot as bot_blueprint
    app.register_blueprint(bot_blueprint, url_prefix='/bot')

    from .game import game as game_blueprint
    app.register_blueprint(game_blueprint, url_prefix='/game')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    # Register main route (optional, for home page)
    @app.route('/')
    def index():
        return "Welcome to ZLX Chatroom System! Please navigate to /chat, /bot, /game, or /admin."

    return app
