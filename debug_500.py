from app import create_app
from app.extensions import db
from app.models import AdminUser

app = create_app()

with app.app_context():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            # Simulate login
            admin = AdminUser.query.filter_by(username='admin').first()
            if admin:
                sess['admin_user_id'] = admin.id
                print(f"Logged in as admin id: {admin.id}")
            else:
                print("Admin user not found!")
                
        try:
            response = client.get('/admin/')
            print(f"Status Code: {response.status_code}")
            if response.status_code == 500:
                print("Error detected!")
        except Exception as e:
            print(f"Exception caught: {e}")
            import traceback
            traceback.print_exc()
