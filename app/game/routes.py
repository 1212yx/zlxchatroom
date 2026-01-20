from flask import render_template
from . import game

@game.route('/')
def index():
    return render_template('game/index.html')
