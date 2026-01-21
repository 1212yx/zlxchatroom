import requests
from app.models import ThirdPartyApi

def get_weather_data(city=None):
    """
    Fetch weather data from external API.
    """
    # 1. Get API config
    api_config = ThirdPartyApi.query.filter_by(command='小天气', is_enabled=True).first()
    
    if not api_config:
        return {'error': '天气接口未配置或已禁用'}

    # 2. Prepare payload
    payload = {
        'token': api_config.token
    }
    
    # If city is provided, we need to know what parameter name to use.
    # Based on common APIs, let's guess 'msg' or 'city'. 
    # The user example shows: '参数名': '参数值'.
    # I'll assume 'msg' is commonly used for these kinds of "chatbot" APIs, 
    # or 'city' if it's strict.
    # Let's try 'msg' first as it often takes natural language like "北京天气" or just "北京".
    if city:
        payload['msg'] = city
    else:
        # If no city, maybe the API uses IP or defaults.
        # Or we can try passing "local" or empty.
        # Let's try passing nothing extra first, or maybe "北京" as default if it fails.
        pass

    try:
        response = requests.post(api_config.url, data=payload, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Log response for debugging (optional)
        print(f"Weather API Response: {data}")
        
        # Check if success
        if data.get('code') == 200:
            # Parse data. Structure depends on actual API response.
            # Assuming standard fields based on user request (icon, temp, humidity, wind, etc.)
            # The example output was just "print(result)", so I have to infer structure or handle generic.
            # Let's return the raw data and let the frontend or a helper format it.
            return data
        else:
            return {'error': data.get('msg', '获取天气失败')}

    except Exception as e:
        print(f"Weather API Error: {e}")
        return {'error': str(e)}

def parse_weather_video(weather_str):
    """
    Map weather description to video filename.
    """
    if not weather_str:
        return None
        
    weather_str = weather_str.lower()
    
    if '雨' in weather_str:
        return 'rain.mp4'
    elif '雪' in weather_str:
        return 'snow.mp4'
    elif '雷' in weather_str:
        return 'thunder.mp4'
    elif '风' in weather_str:
        return 'wind.mp4'
    elif '晴' in weather_str or '云' in weather_str or '阳' in weather_str:
        return 'sun.mp4'
    
    return 'sun.mp4' # Default
