from flask_socketio import emit
from ..extensions import socketio

@socketio.on('message')
def handle_message(message):
    print('Received message: ' + message)
    # 广播消息给所有连接的客户端
    emit('message', message, broadcast=True)

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')
