from flask import render_template
from . import bot

@bot.route('/')
def index():
    return render_template('bot/index.html')
