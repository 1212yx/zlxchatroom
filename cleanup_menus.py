from app import create_app
from app.extensions import db
from app.models import Menu

app = create_app('default')

with app.app_context():
    # IDs to delete: 12, 15, 16 (based on previous check, they have suspicious URLs)
    # Also check if they exist first
    ids_to_delete = [12, 15, 16]
    for mid in ids_to_delete:
        menu = Menu.query.get(mid)
        if menu:
            print(f"Deleting menu: {menu.name} (ID: {menu.id}, URL: {menu.url})")
            db.session.delete(menu)
    
    # Also checking if there are other duplicates
    # We want 'admin.menus' and 'admin.roles'
    
    db.session.commit()
    print("Cleanup complete.")
