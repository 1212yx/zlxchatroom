import requests
from app import create_app
from app.models import AdminUser

app = create_app('default')

# Create a test client
with app.test_client() as client:
    with app.app_context():
        # Login first (mock session)
        with client.session_transaction() as sess:
            admin = AdminUser.query.first()
            if admin:
                sess['admin_user_id'] = admin.id
                print(f"Logged in as admin: {admin.username}")
            else:
                print("No admin user found!")
                exit(1)

    # Request the dashboard stats API
    try:
        response = client.get('/admin/api/dashboard/stats')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response Data:", response.json)
        else:
            print("Error Response:", response.text)
    except Exception as e:
        print(f"Exception: {e}")
