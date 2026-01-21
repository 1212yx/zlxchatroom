from app import create_app
from app.chat.weather import get_weather_data
import sys

# 设置控制台输出编码为 utf-8，防止打印中文乱码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = create_app()

with app.app_context():
    print("Testing get_weather_data('北京')...")
    data = get_weather_data("北京")
    print(f"Result: {data}")
    
    if data.get('data', {}).get('city') == '北京':
        print("SUCCESS: Returned Beijing weather.")
    else:
        print(f"FAILURE: Returned {data.get('data', {}).get('city')} instead of Beijing.")
