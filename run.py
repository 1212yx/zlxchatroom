import os
from app import create_app, socketio

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    print("Starting server on 0.0.0.0:5555...")
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5555)
    except Exception as e:
        print(f"Error: {e}")
    print("Server stopped.")

