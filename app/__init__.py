import os

import eventlet

# hack so that ipython doesn't break when importing from app

ipython = False
try:
    __IPYTHON__
    ipython = True
except NameError:
    eventlet.monkey_patch()

import flask
from flask import Flask, Blueprint, json
from flask_restx import Api
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
import flask_praetorian
import logging
from flask import request
from flask_praetorian import utilities as prae_utils

from app.cloud.utilities import CloudStores
from config import Config
import flask_cors
from flask_buzz import FlaskBuzz
from elasticsearch import Elasticsearch
from engineio.payload import Payload
from rq import Queue
from redis_worker import conn

logging.basicConfig(filename='/dev/null', level=logging.DEBUG)
logger = logging.getLogger()
handler = logging.StreamHandler()

formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('s3transfer').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

app = Flask(__name__, static_folder="site/static", template_folder="site")
flask_version = flask.__version__

app.config.from_object(Config)

app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

db = SQLAlchemy(app, engine_options={"connect_args": {"options": "-c timezone=UTC"}})
ma = Marshmallow(app)
cors = flask_cors.CORS()
cors.init_app(app)

guard = flask_praetorian.Praetorian()

api_version = 'v0.1'

api = Api(app, version='0.1', title='Blood Bike API',
          description='API for use with blood bike dispatching')

login_ns = api.namespace('api/{}/login'.format(api_version), description='Login operations')
user_ns = api.namespace('api/{}/user'.format(api_version), description='User operations')
session_ns = api.namespace('api/{}/session'.format(api_version), description='Session operations')
task_ns = api.namespace('api/{}/task'.format(api_version), description='Task operations')
vehicle_ns = api.namespace('api/{}/vehicle'.format(api_version), description='Vehicle operations')
comment_ns = api.namespace('api/{}/comment'.format(api_version), description='Comment operations')
deliverable_ns = api.namespace('api/{}/deliverable'.format(api_version), description='Deliverable operations')
location_ns = api.namespace('api/{}/location'.format(api_version), description='Saved location operations')
any_object_ns = api.namespace('api/{}/any'.format(api_version), description='Lookup for any object')
log_ns = api.namespace('api/{}/log'.format(api_version), description='Logging lookups')
search_ns = api.namespace('api/{}/search'.format(api_version), description='Elasticsearch functions')
root_ns = api.namespace('api/{}'.format(api_version), description='Root api calls')

Payload.max_decode_packets = 50
socketio = SocketIO(app, cors_allowed_origins='*', message_queue=app.config['REDIS_URL'])


FlaskBuzz.register_error_handler_with_flask_restplus(api)

app.debug = True
migrate = Migrate(app, db)

redis_queue = Queue(connection=conn)

cloud_stores = CloudStores(
    platform=app.config["CLOUD_PLATFORM"],
    profile_picture_store_name=app.config['CLOUD_PROFILE_PICTURE_STORE_NAME'],
    region=app.config['AWS_DEFAULT_REGION'],
    access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    secret_access_key_id=app.config['AWS_SECRET_ACCESS_KEY'],
    endpoint=app.config['AWS_ENDPOINT']
)

# check if the profile picture processing directory exists (unless loading in ipython)
if not ipython:
    profile_pic_dir = app.config['PROFILE_PROCESSING_DIRECTORY']
    if profile_pic_dir:
        if not os.path.isdir(profile_pic_dir):
            os.mkdir(profile_pic_dir)
    else:
        raise EnvironmentError("A profile picture processing directory must be specified.")


from app import models
from app.api.task import task
from app.api.user import user
from app.api.login import login
from app.api.vehicle import vehicle
from app.api.comment import comment
from app.api.deliverable import deliverable
from app.api.location import location
from app.api.search import search
from app.api.log import log
from app.api.priority import priority
from app.api.patch import patch
from app.api.server_settings import server_settings
from app.api import ping
from app.api import redis
from app.api import uuid_lookup
from app.api import sockets

site_blueprint = Blueprint('site', __name__, url_prefix='/')

guard.init_app(app, models.User)
app.register_blueprint(site_blueprint)
#app.register_blueprint(testing_views.mod)


def get_http_code_int(label):
    result = models.HTTPRequestType.query.filter_by(label=label).first()
    return result.id if result else None


def endpoint_to_object_type(endpoint):
    if not endpoint:
        return models.Objects.UNKNOWN
    if "task" in endpoint:
        return models.Objects.TASK
    elif "comment" in endpoint:
        return models.Objects.COMMENT
    elif "deliverable" in endpoint:
        return models.Objects.DELIVERABLE
    elif "location" in endpoint:
        return models.Objects.LOCATION
    elif "user" in endpoint:
        return models.Objects.USER
    elif "vehicle" in endpoint:
        return models.Objects.VEHICLE
    elif "server_settings" in endpoint:
        return models.Objects.SETTINGS
    elif "patch" in endpoint:
        return models.Objects.PATCH
    return models.Objects.UNKNOWN


@app.after_request
def log_input(response):
    if request.method in ["POST", "PUT", "DELETE"]:
        if not request.endpoint.endswith("login_login"):
            try:
                object_uuid = json.loads(response.get_data())['uuid']
            except KeyError:
                object_uuid = None
            token = guard.read_token_from_header()
            if token:
                jwt_data = guard.extract_jwt_token(token)
                user = models.User.query.filter_by(id=jwt_data['id']).one()
                response_status = models.HTTPResponseStatus.query.filter_by(status=int(response.status_code)).first()
                entry = models.LogEntry(
                    parent_type=endpoint_to_object_type(request.endpoint),
                    calling_user_uuid=user.uuid,
                    http_request_type_id=get_http_code_int(request.method),
                    parent_uuid=object_uuid,
                    http_response_status_id=response_status.id if response_status else None
                )
                db.session.add(entry)
                db.session.commit()
            else:
                logger.error("Missing token when attempting to log request.")
    return response


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

