from app import create_app
from app.extensions import db
from app.models import Menu, AdminUser

app = create_app('default')

with app.app_context():
    # 1. Add Menu
    # Check if exists
    menu = Menu.query.filter_by(name='AI分析与报告').first()
    if not menu:
        menu = Menu(
            name='AI分析与报告',
            icon='layui-icon-chart-screen',
            url='admin.ai_analysis',
            parent_id=None,
            order=7,
            is_visible=True
        )
        db.session.add(menu)
        db.session.commit()
        print("Created 'AI分析与报告' menu.")
    else:
        print("Menu 'AI分析与报告' already exists. Updating URL just in case.")
        menu.url = 'admin.ai_analysis'
        db.session.commit()

    # 2. Assign permission to Super Admin (and others if needed, but logic usually auto-includes super)
    # The current logic for Super Admin (is_super=True) automatically gives access to all menus.
    # But for roles, we might need to add it manually if we had roles setup.
    # For now, just ensuring the menu exists is enough for Super Admin.
    
    print("Database updated successfully.")
