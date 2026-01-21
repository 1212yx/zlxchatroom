from app import create_app, db
from app.models import ThirdPartyApi

app = create_app()
with app.app_context():
    configs = ThirdPartyApi.query.all()
    print(f"Found {len(configs)} configs:")
    for c in configs:
        print(f"ID: {c.id}, Command: {c.command}, Enabled: {c.is_enabled}, URL: {c.url}, Token: {c.token}")
