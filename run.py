import eventlet
eventlet.monkey_patch()

import os
import json
from app import create_app

# Load configuration from config.json
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    default_config = {'host': '127.0.0.1', 'port': 8090}
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config.json: {e}")
            return default_config
    return default_config

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    config = load_config()
    host = config.get('host', '127.0.0.1')
    port = config.get('port', 8090)
    print(f"Starting server at {host}:{port}")
    # socketio.run(app, debug=False, use_reloader=False, host=host, port=port)
    app.run(debug=True, use_reloader=False, host=host, port=port)
