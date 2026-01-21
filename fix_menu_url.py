from app import create_app
from app.extensions import db
from app.models import Menu

app = create_app('default')

with app.app_context():
    # Find the menu with the problematic URL
    bad_menu = Menu.query.filter_by(url='/admin/ai-analysis').first()
    if bad_menu:
        print(f"Found problematic menu: {bad_menu.name} (ID: {bad_menu.id}, URL: {bad_menu.url})")
        
        # Check if there are other menus with similar issues
        all_menus = Menu.query.all()
        for m in all_menus:
            if m.url and m.url.startswith('/'):
                 print(f"Suspicious URL format: {m.name} (ID: {m.id}, URL: {m.url})")
                 
        # Delete the specific problematic menu as requested by the error
        db.session.delete(bad_menu)
        db.session.commit()
        print("Deleted problematic menu.")
    else:
        print("Menu with url '/admin/ai-analysis' not found.")
