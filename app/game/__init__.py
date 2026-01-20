from flask import Blueprint

game = Blueprint('game', __name__, template_folder='templates', static_folder='static')

from . import routes
