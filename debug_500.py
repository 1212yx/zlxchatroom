
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
        # Login as admin
        # We need to set the session manually or simulate login
        # Admin login uses session['admin_user_id']
        
        # Find an admin user
        admin = AdminUser.query.first()
        if not admin:
            print("No admin user found!")
            sys.exit(1)
            
        with client.session_transaction() as sess:
            sess['admin_user_id'] = admin.id
            
        print(f"--- Testing /admin/messages with admin id {admin.id} ---")
        try:
            response = client.get('/admin/messages')
            print(f"Status Code: {response.status_code}")
            if response.status_code == 500:
                print("Internal Server Error detected.")
                # The Flask test client usually prints the exception to stderr, 
                # but we can't easily capture that in the tool output unless we redirect stderr.
                # However, create_app usually configures logging.
        except Exception as e:
            print(f"Exception during request: {e}")

        print("\n--- Testing /admin/rooms/1/announce ---")
        try:
            # Assuming room 1 exists
            response = client.post('/admin/rooms/1/announce', data={'content': 'Test Announcement'})
            print(f"Status Code: {response.status_code}")
        except Exception as e:
             print(f"Exception during request: {e}")
