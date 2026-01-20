from app import create_app, db
from app.models import WSServer

app = create_app()

with app.app_context():
    servers = WSServer.query.all()
    updated = False
    for server in servers:
        if '8090' in server.address:
            server.address = server.address.replace('8090', '5555')
            updated = True
        elif '8091' in server.address:
            server.address = server.address.replace('8091', '5556')
            updated = True
        elif '8092' in server.address:
            server.address = server.address.replace('8092', '5557')
            updated = True
            
    if updated:
        db.session.commit()
        print("Updated server ports in database.")
    else:
        print("No servers needed updating.")
