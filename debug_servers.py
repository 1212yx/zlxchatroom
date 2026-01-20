from app import create_app
from flask import url_for

app = create_app()

with app.app_context():
    with app.test_request_context():
        try:
            print(f"Testing render of admin.servers...")
            # We can't easily fully render the template without a real request context with session, 
            # but we can try to verify the URL building which was the previous error.
            print(f"admin.servers URL: {url_for('admin.servers')}")
            
            # Let's check if there are other url_for calls in the template that might be failing.
            # Reading the file content manually to check for other url_for calls.
            import re
            with open(r'c:\Users\在快乐星球度假\Desktop\团队任务\zlxchatroom\app\admin\templates\admin\servers.html', 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(r"url_for\('([^']+)'\)", content)
                print(f"Found url_for endpoints in servers.html: {matches}")
                
                for endpoint in matches:
                    try:
                        print(f"Building {endpoint}: {url_for(endpoint)}")
                    except Exception as e:
                        print(f"Failed to build {endpoint}: {e}")

        except Exception as e:
            print(f"Error: {e}")
