import requests
import json

url = 'http://apii.52vmy.cn/api/music/wy/rand'
token = '270eab1f9444368dcf0a0dc139ccfa50'

def test_post():
    print("Testing POST...")
    try:
        payload = {'token': token}
        response = requests.post(url, data=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"POST Error: {e}")

def test_get():
    print("\nTesting GET...")
    try:
        params = {'token': token}
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"GET Error: {e}")

if __name__ == "__main__":
    test_post()
    test_get()
