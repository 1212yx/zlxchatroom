from app import create_app, db
from app.models import Menu

app = create_app()

with app.app_context():
    menus = Menu.query.filter_by(parent_id=None).order_by(Menu.order).all()
    for menu in menus:
        print(f"[{menu.id}] {menu.name} (Order: {menu.order})")
        for child in menu.children:
            print(f"  - [{child.id}] {child.name} -> {child.url} (Order: {child.order})")
