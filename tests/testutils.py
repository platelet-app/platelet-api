import json
import random
import string
from app import models, db
from uuid import UUID
from haikunator import Haikunator

root_url = "http://localhost:5000/api/v0.1/"
login_url = "{}login".format(root_url)
user_url = "{}user".format(root_url)
session_url = "{}session".format(root_url)
task_url = "{}task".format(root_url)
jwtKey = ""
authHeader = {}
authJsonHeader = {}


def whoami(client, header):
    res = client.get("{}whoami".format(root_url), headers=header)
    return json.loads(res.data)['uuid']

def delete_by_uuid(uuid):
    for enum in models.Objects:
        result = get_object(enum, uuid)
        if result:
            db.session.delete(result)
            db.session.commit()
            return

def generate_name():
    haik = Haikunator()
    return haik.haikunate()

def attr_check(data, obj, exclude=[]):
    for key in data:
        if key not in exclude:
            if not isinstance(data[key], dict):
                assert getattr(obj, key) == data[key]
            else:
                for key_second in data[key]:
                    if key_second not in exclude:
                        if not isinstance(data[key][key_second], dict):
                            assert getattr(getattr(obj, key), key_second) == data[key][key_second]
                        else:
                            for key_third in data[key][key_second]:
                                if key_third not in exclude:
                                    if not isinstance(data[key][key_second][key_third], dict):
                                        assert getattr(getattr(getattr(obj, key), key_second), key_third) == data[key][key_second][key_third]


def get_test_json():
    with open("test_data.json") as f:
        json_data = json.load(f)
    return json_data


def print_response(r):
    print("Status Code: {}, Payload: {}".format(r.status_code,json.loads(r.data)))

def is_json(js):
    try:
        json_object = json.loads(js)
    except Exception as e:
        return False
    return True


def get_user_id(js):
    return json.loads(js)['uuid']


def random_string(length=10):
    return ''.join(random.choice(string.ascii_letters) for m in range(length))


def get_object(type, _id):
    if type == models.Objects.SESSION:
        return models.Session.query.filter_by(uuid=_id).first()
    elif type == models.Objects.USER:
        return models.User.query.filter_by(uuid=_id).first()
    elif type == models.Objects.TASK:
        return models.Task.query.filter_by(uuid=_id).first()
    elif type == models.Objects.VEHICLE:
        return models.Vehicle.query.filter_by(uuid=_id).first()
    elif type == models.Objects.NOTE:
        return models.Note.query.filter_by(uuid=_id).first()
    elif type == models.Objects.DELIVERABLE:
        return models.Deliverable.query.filter_by(uuid=_id).first()
    elif type == models.Objects.LOCATION:
        return models.Location.query.filter_by(uuid=_id).first()
    else:
        return None


def login_as(client, user_type):
    if user_type == "admin":
        login_details = {"username": "test_admin", "password": "9409u8fgrejki0"}
    elif user_type == "coordinator":
        login_details = {"username": "test_coordinator", "password": "9409u8fgrejki0"}
    elif user_type == "rider":
        login_details = {"username": "test_rider", "password": "9409u8fgrejki0"}
    else:
        raise ValueError("invalid user type")

    r = client.post(login_url, data=login_details)
    assert(r.status_code == 200)
    global authJsonHeader
    authJsonHeader = {"Authorization": "Bearer {}".format(json.loads(r.data)['access_token']), 'content-type': 'application/json'}
    global authHeader
    authHeader = {"Authorization": "Bearer {}".format(json.loads(r.data)['access_token'])}

    # TODO also log out again?


def find_user(user_type):
    if user_type == "admin":
        username = "test_admin"
    elif user_type == "coordinator":
        username = "test_coordinator"
    elif user_type == "rider":
        username = "test_admin"
    else:
        raise ValueError("invalid user type")

    user = models.User.query.filter_by(username=username).first()
    return user.uuid

def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except:
        return False

    return str(uuid_obj) == uuid_to_test