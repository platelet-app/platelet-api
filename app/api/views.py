from flask import render_template
from app import app

from app import db

@app.route('/', methods=['GET'])
def hello():
    return render_template('index.html',
                           title="Freewheelers EVS")

