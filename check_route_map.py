from app import create_app
from app.extensions import db
from app.models import Menu

app = create_app('default')

with app.app_context():
    # Check '管理员管理' menu
    menu = Menu.query.filter_by(name='管理员管理').first()
    if menu:
        print(f"Current Menu: {menu.name}, URL: {menu.url}")
        # The error suggests 'admin.admin_list' might be problematic or not found during build if not registered correctly?
        # Actually, the error says: Could not build url for endpoint 'admin.admin_list'. Did you mean 'admin.api_edit'?
        # This usually means 'admin.admin_list' is NOT in the url_map.
        # But we see it in routes.py lines 669-671: @admin.route('/admin-users') -> def admin_list():
        # Wait, if the blueprint is 'admin', the endpoint is 'admin.admin_list'.
        
        # Let's check url map
        print("\nURL Map rules for 'admin.admin_list':")
        rules = [r for r in app.url_map.iter_rules() if r.endpoint == 'admin.admin_list']
        if rules:
            for r in rules:
                print(r)
        else:
            print("No rules found for endpoint 'admin.admin_list'!")
            
    else:
        print("Menu '管理员管理' not found.")
