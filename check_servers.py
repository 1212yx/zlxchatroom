from app import create_app
from app.models import WSServer

app = create_app()

with app.app_context():
    servers = WSServer.query.all()
    print(f"Found {len(servers)} servers.")
    for server in servers:
        print(f"Server {server.id}: created_at={server.created_at}")
        if server.created_at is None:
            print("FOUND SERVER WITH NULL created_at! This will cause the template error.")
