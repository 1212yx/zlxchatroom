from app import create_app
from flask import url_for

app = create_app()

with app.app_context():
    with app.test_request_context():
        print(f"admin.users: {url_for('admin.users')}")
        print(f"admin.index: {url_for('admin.index')}")
        try:
            url_for('admin.user_list')
            print("admin.user_list: EXISTS (Unexpected)")
        except Exception as e:
            print(f"admin.user_list: {e}")
