from flask import Flask, session
from app import create_app
from app.extensions import db
from app.models import Menu

app = create_app('default')

# Mock request context
with app.test_request_context():
    # Mock session
    with app.app_context():
        # Case 1: No login
        session.clear()
        print("--- Testing without login ---")
        # Manually call logic
        if 'admin_user_id' not in session:
            print("Inject Menus: {}")
        else:
            print("Inject Menus: Should not happen")

        # Case 2: Login
        session['admin_user_id'] = 1
        print("\n--- Testing with login ---")
        menus = Menu.query.filter_by(parent_id=None, is_visible=True).order_by(Menu.order).all()
        print(f"Inject Menus Count: {len(menus)}")
        for m in menus:
            print(f"- {m.name} (Children: {len(m.children)})")
