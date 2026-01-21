import requests
from app import create_app
import threading
import time

def test_favicon():
    app = create_app('default')
    # Use test client
    with app.test_client() as client:
        response = client.get('/favicon.ico')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 204:
            print("Success: Favicon 404 error resolved (returning 204 No Content).")
        else:
            print(f"Failure: Expected 204, got {response.status_code}")

if __name__ == "__main__":
    test_favicon()
