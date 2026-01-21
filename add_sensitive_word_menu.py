from app import create_app, db
from app.models import Menu, Role

app = create_app()
with app.app_context():
    # ... (previous code) ...
    
    # Assign to Admin Role
    admin_role = Role.query.filter_by(name='超级管理员').first()
    if not admin_role:
        admin_role = Role.query.filter_by(name='管理员').first()
    
    if admin_role:
        # Get all menus
        parent = Menu.query.filter_by(name='内容安全').first()
        child = Menu.query.filter_by(url='admin.sensitive_words').first()
        
        if parent not in admin_role.menus:
            admin_role.menus.append(parent)
        if child not in admin_role.menus:
            admin_role.menus.append(child)
        
        db.session.commit()
        print(f"Assigned menus to role: {admin_role.name}")
    else:
        print("Admin role not found.")
