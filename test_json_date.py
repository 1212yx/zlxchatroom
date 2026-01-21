import json
from datetime import datetime

class MockMessage:
    def __init__(self):
        self.created_at = datetime.now()

msg = MockMessage()
data = {'created_at': msg.created_at}

try:
    json.dumps(data)
    print("Success")
except TypeError as e:
    print(f"Failed as expected: {e}")

data_fixed = {'created_at': msg.created_at.isoformat()}
json.dumps(data_fixed)
print("Success with fix")
