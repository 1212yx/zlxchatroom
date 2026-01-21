
from app import create_app, db
from app.models import AIModel

app = create_app()
with app.app_context():
    models = AIModel.query.all()
    print(f"Total models: {len(models)}")
    for m in models:
        print(f"ID: {m.id}")
        print(f"  Name: {m.name}")
        print(f"  Model Name: {m.model_name}")
        print(f"  API URL: {m.api_url}")
        print(f"  Enabled: {m.is_enabled}")
