import requests
from app.models import ThirdPartyApi

def get_music_data(command_type):
    """
    Fetch music data from external API.
    command_type: 'gift' or 'random' (mapped to DB command)
    """
    cmd_str = '小音乐 群内送歌' if command_type == 'gift' else '小音乐 随机播放'
    
    # 1. Get API config
    api_config = ThirdPartyApi.query.filter_by(command=cmd_str, is_enabled=True).first()
    
    if not api_config:
        # Fallback to check if the other one exists if this one doesn't (since they share URL)
        api_config = ThirdPartyApi.query.filter(ThirdPartyApi.command.like('小音乐%')).first()
        if not api_config:
            return {'error': '音乐接口未配置'}

    # 2. Prepare payload
    payload = {
        'token': api_config.token
    }
    
    try:
        response = requests.post(api_config.url, data=payload, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        # Log for debug
        print(f"Music API Response: {data}")
        
        if data.get('code') == 200:
            return data
        else:
            return {'error': data.get('msg', '获取音乐失败')}

    except Exception as e:
        print(f"Music API Error: {e}")
        return {'error': str(e)}
