from app import create_app, db
from app.models import ThirdPartyApi

app = create_app()

with app.app_context():
    # 1. Group Song Gift
    existing = ThirdPartyApi.query.filter_by(command='小音乐 群内送歌').first()
    if existing:
        print("Music Gift interface already exists. Updating...")
        existing.name = '小音乐 群内送歌'
        existing.url = 'http://apii.52vmy.cn/api/music/wy/rand'
        existing.token = '270eab1f9444368dcf0a0dc139ccfa50'
        existing.is_enabled = True
    else:
        print("Creating Music Gift interface...")
        api = ThirdPartyApi(
            name='小音乐 群内送歌',
            command='小音乐 群内送歌',
            url='http://apii.52vmy.cn/api/music/wy/rand',
            token='270eab1f9444368dcf0a0dc139ccfa50',
            is_enabled=True
        )
        db.session.add(api)
    
    # 2. Random Play (Private)
    existing_rand = ThirdPartyApi.query.filter_by(command='小音乐 随机播放').first()
    if existing_rand:
        print("Music Random interface already exists. Updating...")
        existing_rand.name = '小音乐 随机播放'
        existing_rand.url = 'http://apii.52vmy.cn/api/music/wy/rand'
        existing_rand.token = '270eab1f9444368dcf0a0dc139ccfa50'
        existing_rand.is_enabled = True
    else:
        print("Creating Music Random interface...")
        api_rand = ThirdPartyApi(
            name='小音乐 随机播放',
            command='小音乐 随机播放',
            url='http://apii.52vmy.cn/api/music/wy/rand',
            token='270eab1f9444368dcf0a0dc139ccfa50',
            is_enabled=True
        )
        db.session.add(api_rand)

    db.session.commit()
    print("Music APIs configured.")
