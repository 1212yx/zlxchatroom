from app import create_app, db
from app.models import Menu

app = create_app()
with app.app_context():
    # Find '群聊天记录'
    chat_menu = Menu.query.filter_by(name='群聊天记录').first()
    # Find '后台采集'
    collection_menu = Menu.query.filter_by(name='后台采集').first()
    
    if chat_menu and collection_menu:
        print(f"Moving '{chat_menu.name}' (ID: {chat_menu.id}) from Parent ID {chat_menu.parent_id} to {collection_menu.id} ('{collection_menu.name}')")
        chat_menu.parent_id = collection_menu.id
        # Adjust order to be after Room Management (usually order 1)
        chat_menu.order = 2 
        
        # Shift others if needed?
        # Room Management is order 1
        # WS Server is order 2 -> make it 3
        # Room File is order 3 -> make it 4
        
        ws_server = Menu.query.filter_by(name='ws服务器管理').first()
        if ws_server:
            ws_server.order = 3
            
        room_file = Menu.query.filter_by(name='群文件管理').first()
        if room_file:
            room_file.order = 4
            
        db.session.commit()
        print("Menu hierarchy updated successfully.")
    else:
        print("Could not find necessary menus.")
