import requests
import json

url = 'http://apii.52vmy.cn/api/music/wy/rand'
token = '270eab1f9444368dcf0a0dc139ccfa50'

payload = {
    'token': token
}

print(f"Testing API: {url}")
print(f"Token: {token}")

try:
    # Try 1: Standard POST data
    print("\n--- Attempt 1: POST data ---")
    response = requests.post(url, data=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {json.dumps(response.json(), ensure_ascii=False)}")
    except:
        print(f"Response Text: {response.text}")

    # Try 2: GET (Just in case)
    print("\n--- Attempt 2: GET with params ---")
    response = requests.get(url, params=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {json.dumps(response.json(), ensure_ascii=False)}")
    except:
        print(f"Response Text: {response.text}")

except Exception as e:
    print(f"Error: {e}")
