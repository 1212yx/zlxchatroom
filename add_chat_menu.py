from app import create_app, db
from app.models import Menu

app = create_app()
with app.app_context():
    # 1. Add "Group Chat History" menu
    # Check if exists
    chat_menu = Menu.query.filter_by(url='admin.messages').first()
    if chat_menu:
        print("Menu '群聊天记录' already exists.")
    else:
        # Try to find '房间管理' parent
        # Note: '房间管理' might be a top level menu without URL, or with URL.
        # Let's search by name.
        room_menu = Menu.query.filter_by(name='房间管理').first()
        parent_id = None
        if room_menu:
            parent_id = room_menu.id
            print(f"Found '房间管理' parent id: {parent_id}")
        else:
            # Try '系统管理'
            sys_menu = Menu.query.filter_by(name='系统管理').first()
            if sys_menu:
                parent_id = sys_menu.id
                print(f"Found '系统管理' parent id: {parent_id}")
            else:
                print("No suitable parent found. Creating top level menu.")
        
        new_menu = Menu(
            name='群聊天记录',
            icon='layui-icon-dialogue',
            url='admin.messages',
            parent_id=parent_id,
            order=10,
            is_visible=True
        )
        db.session.add(new_menu)
        db.session.commit()
        print("Created '群聊天记录' menu.")
