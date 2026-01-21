from app import create_app, db
from app.models import ThirdPartyApi

app = create_app()

with app.app_context():
    # Drop the table if it exists to ensure schema is up to date
    ThirdPartyApi.__table__.drop(db.engine, checkfirst=True)
    db.create_all()
    
    # Check if we have APIs
    if ThirdPartyApi.query.count() == 0:
        apis = [
            {
                "name": "天气查询",
                "command": "@天气",
                "url": "https://api.weatherapi.com/v1/current.json?q={city}",
                "token": "your_api_key_here",
                "is_enabled": True
            },
            {
                "name": "每日新闻",
                "command": "@新闻",
                "url": "https://newsapi.org/v2/top-headlines?country=cn",
                "token": "news_api_token",
                "is_enabled": True
            },
            {
                "name": "音乐搜索",
                "command": "@音乐",
                "url": "https://api.music.com/search?q={query}",
                "token": "",
                "is_enabled": False
            },
            {
                "name": "电影推荐",
                "command": "@电影",
                "url": "https://api.movie.com/recommend",
                "token": "",
                "is_enabled": True
            },
            {
                "name": "股票查询",
                "command": "@股票",
                "url": "https://api.stock.com/quote?symbol={symbol}",
                "token": "stock_api_token",
                "is_enabled": True
            },
            {
                "name": "笑话大全",
                "command": "@笑话",
                "url": "https://api.jokes.com/random",
                "token": "",
                "is_enabled": True
            }
        ]
        
        for data in apis:
            api = ThirdPartyApi(
                name=data['name'],
                command=data['command'],
                url=data['url'],
                token=data['token'],
                is_enabled=data['is_enabled']
            )
            db.session.add(api)
        
        db.session.commit()
        print(f"Created {len(apis)} dummy APIs.")
    else:
        print("APIs already exist.")
