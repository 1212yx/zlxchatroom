from app import create_app, db
from app.models import WSServer

app = create_app()

with app.app_context():
    servers = WSServer.query.all()
    updated = False
    for server in servers:
        # Update all to 5555
        new_addr = 'ws://127.0.0.1:5555/chat/ws'
        if server.address != new_addr:
            print(f"Updating {server.name}: {server.address} -> {new_addr}")
            server.address = new_addr
            updated = True
            
    if updated:
        db.session.commit()
        print("Updated server ports in database to 5555.")
    else:
        print("No servers needed updating.")
from app import create_app, db
from app.models import WSServer

app = create_app()

with app.app_context():
    servers = WSServer.query.all()
    updated = False
    for server in servers:
        if '5555' in server.address:
            server.address = server.address.replace('5555', '8090/chat/ws')
            updated = True
        elif '5556' in server.address:
            server.address = server.address.replace('5556', '8090/chat/ws')
            updated = True
        elif '5557' in server.address:
            server.address = server.address.replace('5557', '8090/chat/ws')
            updated = True
            
    if updated:
        db.session.commit()
        print("Updated server ports in database.")
    else:
        print("No servers needed updating.")
