from app import create_app
from app.models import Menu

app = create_app('default')

with app.app_context():
    menus = Menu.query.all()
    print(f"Total menus found: {len(menus)}")
    for m in menus:
        print(f"ID: {m.id}, Name: {m.name}, Parent: {m.parent_id}, Order: {m.order}, Visible: {m.is_visible}, URL: {m.url}")
