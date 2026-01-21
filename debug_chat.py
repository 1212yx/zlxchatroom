import json
from flask import Flask, session
from app import create_app, db
from app.models import AdminUser, AIModel, AIChatSession, AIChatMessage
from app.services.ai_analysis import AIAnalysisService
from datetime import datetime

app = create_app()

def debug_chat_route():
    with app.app_context():
        # Setup context
        admin = AdminUser.query.first()
        if not admin:
            print("No admin user found")
            return
            
        model = AIModel.query.filter_by(is_enabled=True).first()
        if not model:
            print("No enabled AI model found")
            return
            
        print(f"Testing with Admin: {admin.username} (ID: {admin.id})")
        print(f"Testing with Model: {model.name} (ID: {model.id})")
        
        # Mock session
        # Since we can't easily mock flask.session inside the route without a request,
        # we will manually execute the logic from the route here.
        
        # Scenario 1: New Session
        print("\n--- Scenario 1: New Session ---")
        message = "Hello Test"
        model_id = model.id
        
        try:
            chat_session = AIChatSession(
                user_id=admin.id,
                title=message[:20],
                ai_model_id=model_id
            )
            db.session.add(chat_session)
            db.session.commit()
            print(f"Session created: ID {chat_session.id}")
            
            user_msg = AIChatMessage(
                session_id=chat_session.id,
                role='user',
                content=message
            )
            db.session.add(user_msg)
            db.session.commit()
            print("User message saved")
            
            messages = [{'role': 'user', 'content': message}]
            
            service = AIAnalysisService(model_id)
            print("Service initialized")
            
            print("Starting stream...")
            for chunk in service.chat_stream(messages, session_id=chat_session.id):
                # print(chunk, end='') 
                pass
            print("\nStream finished")
            
        except Exception as e:
            print(f"ERROR in Scenario 1: {e}")
            import traceback
            traceback.print_exc()

        # Scenario 2: Existing Session
        print("\n--- Scenario 2: Existing Session ---")
        session_id = chat_session.id
        message = "Follow up"
        
        try:
            chat_session = AIChatSession.query.get(session_id)
            if chat_session and chat_session.user_id == admin.id:
                user_msg = AIChatMessage(
                    session_id=session_id,
                    role='user',
                    content=message
                )
                db.session.add(user_msg)
                chat_session.updated_at = datetime.utcnow()
                db.session.commit()
                print("User message saved")
                
                db_history = chat_session.messages.order_by(AIChatMessage.created_at.desc()).limit(20).all()
                db_history_reversed = db_history[::-1]
                
                messages = []
                for m in db_history_reversed:
                    messages.append({'role': m.role, 'content': m.content})
                    
                print(f"History loaded: {len(messages)} messages")
                
                service = AIAnalysisService(model_id)
                print("Starting stream...")
                for chunk in service.chat_stream(messages, session_id=session_id):
                    pass
                print("\nStream finished")
                
        except Exception as e:
            print(f"ERROR in Scenario 2: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    debug_chat_route()
