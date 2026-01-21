from app import create_app, db
from app.models import WSServer
from flask import render_template

app = create_app()

with app.app_context():
    with app.test_request_context('/admin/servers'):
        try:
            # Mock pagination object
            class MockPagination:
                def __init__(self, items):
                    self.items = items
                    self.total = len(items)
                    self.page = 1
                    self.per_page = 12
                    self.pages = 1

            servers = WSServer.query.all()
            pagination = MockPagination(servers)
            
            # Try to render the template
            print("Rendering template...")
            rendered = render_template('admin/servers.html', servers=servers, pagination=pagination)
            print("Template rendered successfully.")
        except Exception as e:
            print(f"Template rendering failed: {e}")
            import traceback
            traceback.print_exc()
