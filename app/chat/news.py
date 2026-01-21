import requests
from app.models import ThirdPartyApi

def get_news_data():
    """
    Fetch news data from external API.
    """
    # 1. Get API config (Default if not found)
    url = 'https://news.topurl.cn/api?count=20'
    token = '270eab1f9444368dcf0a0dc139ccfa50' # Default token if needed, though this API seems public or uses IP

    api_config = ThirdPartyApi.query.filter_by(command='小新闻', is_enabled=True).first()
    if api_config:
        url = api_config.url
        # Token might not be needed for this specific API based on the URL structure, 
        # but we preserve logic for consistency if user configures it.
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') == 200:
            return data
        else:
            return {'error': data.get('msg', '获取新闻失败')}

    except Exception as e:
        print(f"News API Error: {e}")
        return {'error': str(e)}
