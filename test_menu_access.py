from app import create_app, db
from app.models import AdminUser, Menu

app = create_app()
ctx = app.app_context()
ctx.push()

current_admin = AdminUser.query.get(1) # admin

# 模拟 inject_menus 的逻辑 (已去掉 is_super 判断)
accessible_menu_ids = set()
for role in current_admin.roles:
    for menu in role.menus:
        accessible_menu_ids.add(menu.id)

all_top_menus = Menu.query.filter_by(parent_id=None, is_visible=True).order_by(Menu.order).all()
final_menus = []

print(f"User: {current_admin.username}, Is Super: {current_admin.is_super}")
print(f"Accessible Menu IDs: {accessible_menu_ids}")

for menu in all_top_menus:
    has_access = menu.id in accessible_menu_ids
    
    visible_children = []
    for child in menu.children:
        if child.id in accessible_menu_ids and child.is_visible:
            visible_children.append(child)
    
    if has_access or visible_children:
        print(f"Visible Menu: {menu.name}")
        for child in visible_children:
            print(f"  - {child.name}")
