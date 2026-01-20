import os
from app import create_app, socketio

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=False, host='127.0.0.1', port=5555)
