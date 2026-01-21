from app import create_app
from app.extensions import db
from app.models import Menu

app = create_app('default')

def init_menus():
    with app.app_context():
        # Clear existing menus to avoid duplicates (optional, careful with IDs)
        # db.session.query(Menu).delete()
        
        if Menu.query.first():
            print("Menus already exist. Skipping initialization.")
            return

        menus = [
            {
                'name': '控制台',
                'icon': 'layui-icon-home',
                'url': 'admin.index',
                'order': 1,
                'children': []
            },
            {
                'name': '用户管理',
                'icon': 'layui-icon-user',
                'url': None,
                'order': 2,
                'children': [
                    {'name': '用户列表', 'icon': '', 'url': 'admin.users', 'order': 1}
                ]
            },
            {
                'name': '后台采集',
                'icon': 'layui-icon-app',
                'url': None,
                'order': 3,
                'children': [
                    {'name': '房间管理', 'icon': '', 'url': 'admin.rooms', 'order': 1},
                    {'name': 'ws服务器管理', 'icon': '', 'url': 'admin.servers', 'order': 2}
                ]
            },
            {
                'name': 'AI模型引擎',
                'icon': 'layui-icon-engine',
                'url': 'admin.ai_models',
                'order': 4,
                'children': []
            },
            {
                'name': '接口管理',
                'icon': 'layui-icon-link',
                'url': 'admin.apis',
                'order': 5,
                'children': []
            }
        ]

        for m_data in menus:
            menu = Menu(
                name=m_data['name'],
                icon=m_data['icon'],
                url=m_data['url'],
                order=m_data['order']
            )
            db.session.add(menu)
            db.session.flush() # get id

            for child_data in m_data['children']:
                child = Menu(
                    name=child_data['name'],
                    icon=child_data['icon'],
                    url=child_data['url'],
                    order=child_data['order'],
                    parent_id=menu.id
                )
                db.session.add(child)
        
        db.session.commit()
        print("Menus initialized successfully.")

if __name__ == '__main__':
    init_menus()
