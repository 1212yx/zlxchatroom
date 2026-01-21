from app import create_app
from app.extensions import db
from app.models import Menu

app = create_app('default')

with app.app_context():
    # Search for the menu item with the problematic URL
    problematic_menu = Menu.query.filter_by(url='admin.sensitive_words').first()
    
    if problematic_menu:
        print(f"Found problematic menu item: ID={problematic_menu.id}, Name='{problematic_menu.name}', URL='{problematic_menu.url}'")
        
        # Delete the menu item
        db.session.delete(problematic_menu)
        db.session.commit()
        print("Successfully deleted the problematic menu item.")
    else:
        print("No menu item found with URL 'admin.sensitive_words'.")
        
        # Double check all menus
        print("Listing all menu URLs:")
        menus = Menu.query.all()
        for m in menus:
            print(f" - {m.name}: {m.url}")
