import json
import random
import string
from app import models, db, schemas
from uuid import UUID
from haikunator import Haikunator


root_url = "http://localhost:5000/api/v0.1/"
login_url = "{}login".format(root_url)
user_url = "{}user".format(root_url)
session_url = "{}session".format(root_url)
vehicle_url = "{}vehicle".format(root_url)
comment_url = "{}comment".format(root_url)
location_url = "{}location".format(root_url)
task_url = "{}task".format(root_url)
mailing_list_url = "{}mailing_list".format(root_url)


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

def dict_check(data, compare, exclude=[]):
    for i in exclude:
        try:
            del data[i]
        except KeyError:
            print("Tried to exclude non existent key")

    return data == compare

def attr_check(data, obj, exclude=[]):
    for key in data:
        if key not in exclude:
            if not isinstance(data[key], dict):
                print(key)
                if key == "uuid":
                    assert str(getattr(obj, key)) == str(data[key])
                else:
                    assert getattr(obj, key) == data[key]
            else:
                for key_second in data[key]:
                    if key_second not in exclude:
                        if not isinstance(data[key][key_second], dict):
                            print(key_second)
                            assert getattr(getattr(obj, key), key_second) == data[key][key_second]
                        else:
                            for key_third in data[key][key_second]:
                                if key_third not in exclude:
                                    if not isinstance(data[key][key_second][key_third], dict):
                                        print(key_third)
                                        assert getattr(getattr(getattr(obj, key), key_second), key_third) == data[key][key_second][key_third]


def get_test_json():
    with open("test_data.json") as f:
        json_data = json.load(f)
    return json_data



def get_object(type, _id, with_deleted=True):
    if with_deleted:
        if type == models.Objects.USER:
            return models.User.query.with_deleted().filter_by(uuid=_id).first()
        elif type == models.Objects.TASK:
            return models.Task.query.with_deleted().filter_by(uuid=_id).first()
        elif type == models.Objects.VEHICLE:
            return models.Vehicle.query.with_deleted().filter_by(uuid=_id).first()
        elif type == models.Objects.COMMENT:
            return models.Comment.query.with_deleted().filter_by(uuid=_id).first()
        elif type == models.Objects.DELIVERABLE:
            return models.Deliverable.query.with_deleted().filter_by(uuid=_id).first()
        elif type == models.Objects.LOCATION:
            return models.Location.query.with_deleted().filter_by(uuid=_id).first()
        else:
            return None
    else:
        if type == models.Objects.USER:
            return models.User.query.filter_by(uuid=_id).first()
        elif type == models.Objects.TASK:
            return models.Task.query.filter_by(uuid=_id).first()
        elif type == models.Objects.VEHICLE:
            return models.Vehicle.query.filter_by(uuid=_id).first()
        elif type == models.Objects.COMMENT:
            return models.Comment.query.filter_by(uuid=_id).first()
        elif type == models.Objects.DELIVERABLE:
            return models.Deliverable.query.filter_by(uuid=_id).first()
        elif type == models.Objects.LOCATION:
            return models.Location.query.filter_by(uuid=_id).first()
        else:
            return None


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except:
        return False

    return str(uuid_obj) == uuid_to_test


def create_task_obj(**kwargs):
    parent = models.TasksParent(reference="TEST-1234")
    db.session.add(parent)
    db.session.flush()
    schema = schemas.TaskSchema()
    task_data = dict(**get_test_json()['task_data'], order_in_relay=1, parent_id=parent.id, **kwargs)
    task = schema.load(task_data)
    return task


def create_user_obj(**kwargs):
    schema = schemas.UserSchema()
    user = schema.load(dict(**get_test_json()['user'], username=generate_name(), display_name=generate_name(), **kwargs))
    return user


def create_vehicle_obj(**kwargs):
    schema = schemas.VehicleSchema()
    vehicle = schema.load(dict(**get_test_json()['vehicle_data'], name=generate_name(), **kwargs))
    return vehicle


def create_location_obj(**kwargs):
    schema = schemas.LocationSchema()
    location = schema.load(dict(**get_test_json()['location_data'], name=generate_name(), **kwargs))
    return location
