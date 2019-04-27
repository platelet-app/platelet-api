from flask import render_template, Blueprint
from app import app

from app import db

mod = Blueprint('test', __name__, url_prefix='/test')

@mod.route('/', methods=['GET'])
def hello():
    return render_template('test_suite.html',
                           title="Freewheelers EVS")
