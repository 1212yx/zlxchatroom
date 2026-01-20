from flask import Blueprint, session

admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')

from . import routes
from ..models import AdminUser

# 注册 session 变量，使模板可以直接访问
@admin.context_processor
def inject_admin_user():
    user_id = session.get('admin_user_id')
    current_admin = None
    if user_id:
        current_admin = AdminUser.query.get(user_id)
    return dict(current_admin=current_admin)
