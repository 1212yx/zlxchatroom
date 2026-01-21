
from app import create_app, db
from app.models import WSServer

app = create_app()

with app.app_context():
    server = WSServer.query.first()
    if not server:
        print("No servers found. Creating default server...")
        default_server = WSServer(
            name='默认服务器',
            address='127.0.0.1:5555',
            description='Default Local Server',
            is_active=True
        )
        db.session.add(default_server)
        db.session.commit()
        print("Default server created.")
    else:
        print(f"Server found: {server.name} ({server.address})")
