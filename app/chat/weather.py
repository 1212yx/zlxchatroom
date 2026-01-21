import requests
from datetime import datetime
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
    
    # Use 'city' parameter for city name (verified by testing)
    if city:
        payload['city'] = city
    else:
        # Default to Neijiang if no city provided (though logic is also in routes)
        payload['city'] = "内江"

    try:
        # Switch to GET request as per API testing
        response = requests.get(api_config.url, params=payload, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Log response for debugging
        print(f"Weather API Response: {data}")
        
        # Check if success
        if data.get('code') == 200:
            # Normalize data for frontend compatibility
            # Frontend expects: data.data.type, data.data.city, data.data.wendu, data.data.fengxiang
            api_data = data.get('data', {})
            
            # Prioritize 'current' data for real-time accuracy, but keep top-level data as fallback
            # User feedback indicates preference for real-time data (e.g., 'current' field)
            current_data = api_data.get('current', {})
            
            # Create a merged data source: start with top-level, then override with current
            source_data = api_data.copy()
            if current_data:
                source_data.update(current_data)
            
            # Extract and transform
            weather_type = source_data.get('weather', '未知')
            # city is usually 'address' in top level, or 'city'
            city_name = source_data.get('address') or source_data.get('city') or city or '未知'
            
            # Handle temperature (strip ℃ if present)
            temp = source_data.get('temp', '')
            if isinstance(temp, str):
                temp = temp.replace('℃', '').replace('°C', '')
            
            # Combine wind info
            # Top level uses wind/windSpeed, current uses wind/windSpeed (but sometimes different keys)
            # Checked log: current has 'wind' and 'windSpeed'
            wind_dir = source_data.get('windDirection') or source_data.get('wind') or ''
            wind_pow = source_data.get('windPower') or source_data.get('windSpeed') or ''
            wind = f"{wind_dir} {wind_pow}".strip()
            
            normalized_data = {
                'code': 200,
                'data': {
                    'type': weather_type,
                    'city': city_name,
                    'wendu': temp,
                    'fengxiang': wind,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    # Keep original data just in case
                    'raw': api_data
                }
            }
            return normalized_data
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
    elif '晴' in weather_str or '阳' in weather_str:
        return 'sun.mp4'
    elif '云' in weather_str or '阴' in weather_str:
        return 'cloud.mp4'
    
    return 'sun.mp4' # Default

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
