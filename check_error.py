import requests

s = requests.Session()
base_url = 'http://127.0.0.1:5555'

# Login
login_url = f'{base_url}/admin/login'
try:
    # Get CSRF token if needed (Flask-WTF), but here it seems simple form
    r = s.get(login_url)
    
    data = {
        'username': 'test_admin',
        'password': '123456'
    }
    r = s.post(login_url, data=data)
    print(f"Login status: {r.status_code}")
    if 'admin_user_id' not in r.text and r.url != f'{base_url}/admin/':
        # Check if redirected to index
        pass

    # Access servers
    print("Checking servers page...")
    servers_url = f'{base_url}/admin/servers'
    r = s.get(servers_url)
    print(f"Servers page status: {r.status_code}")
    if r.status_code != 200:
        print(r.text[:2000])

    # Access users
    print("Checking users page...")
    users_url = f'{base_url}/admin/users'
    r = s.get(users_url)
    print(f"Users page status: {r.status_code}")
    if r.status_code != 200:
        print(r.text[:2000])

    # Access apis
    print("Checking apis page...")
    apis_url = f'{base_url}/admin/apis'
    r = s.get(apis_url)
    print(f"APIs page status: {r.status_code}")
    if r.status_code != 200:
        print(r.text[:2000])
        
    # Try adding an API
    print("Testing Add API...")
    add_api_url = f'{base_url}/admin/apis/add'
    data = {
        'name': 'Test Weather',
        'command': '@weather_test_2', # Changed command to avoid duplicate
        'url': 'http://api.weather.com',
        'token': '123456'
    }
    r = s.post(add_api_url, data=data)
    print(f"Add API status: {r.status_code}")
    print(f"Add API response: {r.text}")



except Exception as e:
    print(f"Error: {e}")
