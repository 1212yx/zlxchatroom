from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sock import Sock
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
sock = Sock()
socketio = SocketIO()
