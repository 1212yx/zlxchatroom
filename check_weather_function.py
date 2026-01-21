
from app import create_app
from app.chat.weather import get_weather_data
import json

app = create_app()

with app.app_context():
    print("Testing get_weather_data('内江')...")
    data = get_weather_data("内江")
    print(f"Result: {json.dumps(data, ensure_ascii=False, indent=2)}")
