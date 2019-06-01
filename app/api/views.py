from flask import render_template
from app import app
import flask_praetorian

from app import db

@app.route('/', methods=['GET'])
def hello():
    return render_template('index.html',
                           title="Freewheelers EVS")

