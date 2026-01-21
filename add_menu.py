from app import create_app
from app.extensions import db
from app.models import Menu, Role

app = create_app()

with app.app_context():
    # Check if menu exists
    menu_name = "可视化大屏"
    menu = Menu.query.filter_by(name=menu_name).first()
    
    if not menu:
        print(f"Creating menu '{menu_name}'...")
        menu = Menu(
            name=menu_name,
            icon="layui-icon-chart-screen",
            url="admin.dashboard",
            order=1, # High priority
            is_visible=True
        )
        db.session.add(menu)
        db.session.commit()
        print(f"Menu '{menu_name}' created with ID {menu.id}")
    else:
        print(f"Menu '{menu_name}' already exists.")
        # Update url just in case
        menu.url = "admin.dashboard"
        menu.icon = "layui-icon-chart-screen"
        db.session.commit()

    # Assign to Super Admin Role (usually id=1 or name='Super Admin')
    # Let's find a role that looks like super admin
    role = Role.query.filter(Role.name.ilike('%admin%')).first()
    if role:
        if menu not in role.menus:
            role.menus.append(menu)
            db.session.commit()
            print(f"Assigned menu to role '{role.name}'")
        else:
            print(f"Menu already assigned to role '{role.name}'")
    else:
        print("No Admin role found. Please assign manually.")
