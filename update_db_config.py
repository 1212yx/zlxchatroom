from app import create_app, db
from app.models import ThirdPartyApi

app = create_app()
with app.app_context():
    # Update ID 4
    config4 = ThirdPartyApi.query.get(4)
    if config4:
        config4.url = 'http://apii.52vmy.cn/api/music/wy/rand'
        print(f"Updated config 4 to {config4.url}")

    # Update ID 5
    config5 = ThirdPartyApi.query.get(5)
    if config5:
        config5.url = 'http://apii.52vmy.cn/api/music/wy/rand'
        print(f"Updated config 5 to {config5.url}")
    
    db.session.commit()
    print("Database updated successfully.")
