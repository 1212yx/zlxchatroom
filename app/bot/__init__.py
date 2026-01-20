from flask import Blueprint

bot = Blueprint('bot', __name__, template_folder='templates', static_folder='static')

from . import routes
