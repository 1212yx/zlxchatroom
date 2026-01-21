
from app import create_app, db
from app.models import ThirdPartyApi
import json

app = create_app()
with app.app_context():
    print("Checking ThirdPartyApi...")
    api = ThirdPartyApi.query.filter_by(command='小视频 url').first()
    if api:
        print(f"API Found: {api.command}, URL: {api.url}, Enabled: {api.is_enabled}")
        
        content = '小视频 https://www.bilibili.com/video/BV1BNkuBFEXP'
        video_url = None
        if content.startswith('小视频 '):
             video_url = content[4:].strip()
        
        print(f"Parsed URL: {video_url}")
        
        if video_url and api.is_enabled:
            parsing_url = api.url
            iframe_src = f"{parsing_url}{video_url}"
            special_payload = {
                'type': 'video_embed',
                'data': {
                    'src': iframe_src,
                    'original_url': video_url
                }
            }
            special_content = "SPECIAL:" + json.dumps(special_payload)
            print(f"Generated Content: {special_content}")
    else:
        print("API NOT FOUND")
