from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_sock import Sock

db = SQLAlchemy()
socketio = SocketIO()
migrate = Migrate()
sock = Sock()
