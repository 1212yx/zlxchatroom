
import os
import sys
from flask import Flask, session
from app import create_app, db
from app.models import AdminUser

# Create a minimal test client
app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.test_client() as client:
    with app.app_context():
        # Find an admin user
        admin = AdminUser.query.first()
        if not admin:
            print("No admin user found!")
            sys.exit(1)
            
        with client.session_transaction() as sess:
            sess['admin_user_id'] = admin.id
            
        print(f"--- Testing /admin/ai-analysis with admin id {admin.id} ---")
        try:
            response = client.get('/admin/ai-analysis')
            print(f"Status Code: {response.status_code}")
            if response.status_code == 500:
                print("Internal Server Error detected.")
        except Exception as e:
            print(f"Exception during request: {e}")
