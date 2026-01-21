from app import create_app
from app.extensions import db
from app.models import Menu

app = create_app('default')

def update_menus():
    with app.app_context():
        # Check if System Management exists
        sys_menu = Menu.query.filter_by(name='系统管理').first()
        if not sys_menu:
            sys_menu = Menu(name='系统管理', icon='layui-icon-set', order=99)
            db.session.add(sys_menu)
            db.session.flush()
            print("Created '系统管理' menu.")
        
        # Add Menu Management
        menu_mgmt = Menu.query.filter_by(url='admin.menus').first()
        if not menu_mgmt:
            menu_mgmt = Menu(name='菜单管理', icon='', url='admin.menus', parent_id=sys_menu.id, order=1)
            db.session.add(menu_mgmt)
            print("Created '菜单管理' menu.")

        # Add Role Management
        role_mgmt = Menu.query.filter_by(url='admin.roles').first()
        if not role_mgmt:
            role_mgmt = Menu(name='角色管理', icon='', url='admin.roles', parent_id=sys_menu.id, order=2)
            db.session.add(role_mgmt)
            print("Created '角色管理' menu.")
            
        db.session.commit()
        print("Menus updated successfully.")

if __name__ == '__main__':
    update_menus()
