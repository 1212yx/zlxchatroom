from app import create_app, db
from app.models import Menu, AdminUser

app = create_app()
with app.app_context():
    print("--- Checking Menus ---")
    menus = Menu.query.all()
    for m in menus:
        parent_name = m.parent.name if m.parent else "None"
        print(f"ID: {m.id}, Name: {m.name}, URL: {m.url}, Parent: {parent_name} (ID: {m.parent_id}), Visible: {m.is_visible}, Order: {m.order}")

    print("\n--- Checking '群聊天记录' specifically ---")
    chat_menu = Menu.query.filter_by(name='群聊天记录').first()
    if chat_menu:
        print(f"Found! ID: {chat_menu.id}, ParentID: {chat_menu.parent_id}")
    else:
        print("Not Found!")

    print("\n--- Checking Admin User ---")
    admin = AdminUser.query.filter_by(username='admin').first()
    if admin:
        print(f"Admin: {admin.username}, Is Super: {admin.is_super}")
        print("Roles:")
        for r in admin.roles:
            print(f" - {r.name}")
