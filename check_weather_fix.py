import requests
from app import create_app
from app.models import ThirdPartyApi

app = create_app()

with app.app_context():
    api_config = ThirdPartyApi.query.filter_by(command='小天气').first()
    if api_config:
        url = api_config.url
        token = api_config.token
        print(f"Calling API: {url}")
        try:
            response = requests.get(url, params={'token': token, 'msg': '内江'}, timeout=10)
            data = response.json()
            print("Raw Data Keys:", data.get('data', {}).keys())
            if 'data' in data and 'current' in data['data']:
                print("Current Data:", data['data']['current'])
            else:
                print("No 'current' field found.")
                
            print("Top Level Data:", {k:v for k,v in data.get('data', {}).items() if isinstance(v, (str, int))})
        except Exception as e:
            print(e)
