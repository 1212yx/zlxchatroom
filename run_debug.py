import os
from app import create_app, socketio

app = create_app('default')

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5566
    print(f"Starting debug server at {host}:{port}")
    socketio.run(app, debug=True, use_reloader=False, host=host, port=port)
