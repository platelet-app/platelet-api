import os
from flask_login import LoginManager
from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
import logging
from config import Config

logging.basicConfig(filename='/dev/null', level=logging.DEBUG)
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
ma = Marshmallow(app)

api = Api(app, prefix='/api/v0.1')


app.debug = True
migrate = Migrate(app, db)

from app import models
from app.views import task, user, views, site

#app.register_blueprint(task.mod)
app.register_blueprint(user.mod)
app.register_blueprint(site.mod)
#app.register_blueprint(decoder.mod)
#app.register_blueprint(encoder.mod)

#app.run(host='0.0.0.0', debug=True)
