import json
from flask import session
from app import create_app, db
from app.models import AdminUser, AIModel

app = create_app()

def test_route():
    with app.test_client() as client:
        with app.app_context():
            # Setup data
            admin = AdminUser.query.first()
            if not admin:
                print("No admin user found")
                return
            
            model = AIModel.query.filter_by(is_enabled=True).first()
            if not model:
                print("No enabled AI model found")
                return
            model_id = model.id
            
            print(f"Testing with Admin: {admin.username} (ID: {admin.id})")
            admin_id = admin.id

            # Create a dummy session with 'ai' role message to test the fix
            from app.models import AIChatSession, AIChatMessage
            from datetime import datetime
            
            # Create session
            chat_session = AIChatSession(
                user_id=admin_id,
                title="Test Role Fix",
                ai_model_id=model_id
            )
            db.session.add(chat_session)
            db.session.commit()
            
            # Add AI message
            ai_msg = AIChatMessage(
                session_id=chat_session.id,
                role='ai',
                content="I am an AI."
            )
            db.session.add(ai_msg)
            db.session.commit()
            
            session_id = chat_session.id
            print(f"Created test session {session_id} with 'ai' role message.")

        # Mock Login
        with client.session_transaction() as sess:
            sess['admin_user_id'] = admin_id
            
        # Send Request with session_id
        print(f"\nSending POST request to /admin/ai-analysis/chat with session_id={session_id}...")
        response = client.post('/admin/ai-analysis/chat', 
                                json={
                                    'message': 'Hello again',
                                    'model_id': model_id,
                                    'session_id': session_id
                                })
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.content_type}")
        
        if response.status_code != 200:
            print("Response Data (First 500 chars):")
            print(response.data[:500])
        else:
            print("Response is 200 OK. Streaming content...")
            # Read stream
            count = 0
            for line in response.response:
                if count < 5:
                    print(f"Chunk: {line}")
                count += 1
            print("...")

if __name__ == "__main__":
    test_route()
