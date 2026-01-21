from app import create_app
from app.models import ThirdPartyApi

app = create_app()
with app.app_context():
    print(f"ThirdPartyApi: {ThirdPartyApi}")
    print(f"ThirdPartyApi name: {ThirdPartyApi.__tablename__}")
