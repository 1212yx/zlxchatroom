import requests
import json

url = "http://apii.52vmy.cn/api/query/tian"
token = "270eab1f9444368dcf0a0dc139ccfa50"

# Test with Beijing
payload = {
    'token': token,
    'city': '北京'
}

try:
    print(f"Requesting {url}...")
    response = requests.get(url, params=payload, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        api_data = data.get('data', {})
        
        # 打印关键字段
        print(f"Top Level Weather: {api_data.get('weather')}")
        print(f"Top Level Temp: {api_data.get('temp')}")
        print(f"Top Level Wind: {api_data.get('windDirection')} {api_data.get('windPower')}")
        
        current = api_data.get('current', {})
        print(f"Current Weather: {current.get('weather')}")
        print(f"Current Temp: {current.get('temp')}")
        print(f"Current Wind: {current.get('windDirection')} {current.get('windPower')}")
        
        # 模拟 app/chat/weather.py 的解析逻辑
        # 修复逻辑：优先使用 current，但合并 top-level
        current = api_data.get('current', {})
        source_data = api_data.copy()
        if current:
            source_data.update(current)
        
        weather_type = source_data.get('weather', '未知')
        temp = source_data.get('temp', '')
        if isinstance(temp, str):
            temp = temp.replace('℃', '').replace('°C', '')
            
        wind_dir = source_data.get('windDirection') or source_data.get('wind') or ''
        wind_pow = source_data.get('windPower') or source_data.get('windSpeed') or ''
        wind = f"{wind_dir} {wind_pow}".strip()
        
        print("\n最终解析结果:")
        print(f"天气 (weather): {weather_type}")
        print(f"温度 (temp): {temp}")
        print(f"风 (wind): {wind}")
        city_name = source_data.get('address') or source_data.get('city') or '未知'
        print(f"城市 (city): {city_name}")
        
    else:
        print(f"Error: {response.status_code}")
        
except Exception as e:
    print(f"Exception: {e}")
