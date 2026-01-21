from app import create_app, db
from app.models import Menu, Role

app = create_app()

with app.app_context():
    # 1. Find Parent Menu "后台采集"
    parent = Menu.query.filter_by(name='后台采集').first()
    if not parent:
        # If not found, create it or put it under root (not recommended)
        print("Error: Parent menu '后台采集' not found.")
        exit(1)
        
    # 2. Check if "群文件管理" already exists
    existing = Menu.query.filter_by(name='群文件管理').first()
    if existing:
        print("Menu '群文件管理' already exists.")
        new_menu = existing
    else:
        new_menu = Menu(
            name='群文件管理',
            url='admin.room_files',
            parent_id=parent.id,
            icon='layui-icon-file',
            order=3,
            is_visible=True
        )
        db.session.add(new_menu)
        db.session.commit()
        print(f"Menu '群文件管理' created with ID {new_menu.id}.")

    # 3. Assign to all roles (for simplicity, or just Super Admin)
    roles = Role.query.all()
    for role in roles:
        if new_menu not in role.menus:
            role.menus.append(new_menu)
            print(f"Assigned to role: {role.name}")
            
    db.session.commit()
    print("Permissions updated.")
