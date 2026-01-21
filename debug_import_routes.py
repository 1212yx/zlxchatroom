
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.chat import routes
        print("Imported app.chat.routes successfully")
        # Check if ThirdPartyApi is available in routes module namespace
        import app.models
        print(f"ThirdPartyApi in models: {app.models.ThirdPartyApi}")
except Exception as e:
    print(f"Failed to import app.chat.routes: {e}")
    import traceback
    traceback.print_exc()
