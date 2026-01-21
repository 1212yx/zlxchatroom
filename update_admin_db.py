from app import create_app
from app.extensions import db
from app.models import AdminUser, Role, Menu

app = create_app('default')

with app.app_context():
    # Create new tables
    db.create_all()
    
    # Check if 'admin' user exists and make it super admin
    admin = AdminUser.query.filter_by(username='admin').first()
    if admin:
        admin.is_super = True
        db.session.commit()
        print("Updated 'admin' to super user.")
    
    # Check if "管理员管理" menu exists
    admin_menu = Menu.query.filter_by(url='admin.admin_list').first()
    if not admin_menu:
        sys_menu = Menu.query.filter_by(name='系统管理').first()
        if sys_menu:
            admin_menu = Menu(
                name='管理员管理', 
                icon='', 
                url='admin.admin_list', 
                parent_id=sys_menu.id, 
                order=1 # Put it first
            )
            db.session.add(admin_menu)
            db.session.commit()
            print("Created '管理员管理' menu.")

    print("Database updated successfully.")
