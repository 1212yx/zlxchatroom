from app import create_app, db
from app.models import WSServer

app = create_app()

with app.app_context():
    servers = [
        {"name": "本地测试服", "address": "ws://127.0.0.1:8765", "description": "本地开发测试用WebSocket服务器"},
        {"name": "官方一区", "address": "ws://chat.zlx.com:8001", "description": "官方主服务器，稳定"},
        {"name": "官方二区", "address": "ws://chat.zlx.com:8002", "description": "官方备用服务器"},
        {"name": "海外节点", "address": "ws://us.zlx.com:9001", "description": "美国节点，延迟较高"},
        {"name": "内网穿透", "address": "ws://frp.zlx.com:7000", "description": "内网穿透测试"},
        {"name": "IPv6测试", "address": "ws://[::1]:8765", "description": "IPv6连接测试"},
        {"name": "SSL安全服", "address": "wss://secure.zlx.com", "description": "加密连接服务器"},
        {"name": "高并发专线", "address": "ws://vip.zlx.com:8888", "description": "VIP用户专用通道"}
    ]

    for s in servers:
        if not WSServer.query.filter_by(name=s['name']).first():
            server = WSServer(name=s['name'], address=s['address'], description=s['description'])
            db.session.add(server)
    
    db.session.commit()
    print(f"Created {len(servers)} dummy servers.")
