from app import create_app
from app.extensions import db
from app.models import Menu

app = create_app('default')

with app.app_context():
    print("--- Diagnosing Menus ---")
    
    # 1. Check "System Management" existence
    sys_menu = Menu.query.filter_by(name='系统管理').first()
    if not sys_menu:
        print("ERROR: '系统管理' menu not found!")
    else:
        print(f"Found '系统管理': ID={sys_menu.id}, Visible={sys_menu.is_visible}, ParentID={sys_menu.parent_id}")
        
        # 2. Check Children
        print(f"Checking children for ID {sys_menu.id}...")
        # Direct query
        children_query = Menu.query.filter_by(parent_id=sys_menu.id).all()
        print(f"Direct query found {len(children_query)} children:")
        for c in children_query:
            print(f" - ID={c.id}, Name={c.name}, URL={c.url}, Visible={c.is_visible}")
            
        # Relationship access
        print(f"Relationship access (sys_menu.children): {sys_menu.children}")
        try:
            print(f"Children count: {len(sys_menu.children)}")
        except Exception as e:
            print(f"Error accessing children: {e}")

    # 3. Simulate Context Processor
    print("\n--- Simulating Context Processor Query ---")
    top_menus = Menu.query.filter_by(parent_id=None, is_visible=True).order_by(Menu.order).all()
    print(f"Top level menus found: {len(top_menus)}")
    for m in top_menus:
        print(f"Menu: {m.name} (ID: {m.id}, Order: {m.order})")
        if m.name == '系统管理':
            print("  -> THIS IS THE MISSING MENU")
