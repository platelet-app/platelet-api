import json
from tests.testutils import random_string, is_json, user_url, login_url, login_as
import tests.testutils
from app import models
import requests

user_id = -1
username = "{}".format(random_string())

payload = {"name": "Someone Person the 2nd",
           "username": username,
           "password": "yepyepyep", "email": "asdf@asdf.com",
           "dob": "24/11/1987", "status": "active",
           "vehicle": "1", "patch": "north",
           "address1": "123 fake street", "address2": "woopity complex",
           "town": "bristol", "county": "bristol", "postcode": "bs11 3ey",
           "country": "uk", "roles": "admin"}


# Util functions

def add_user(data):
    return requests.post('{}s'.format(user_url), data=json.dumps(data), headers=tests.testutils.authJsonHeader)


# Test functions

def test_login(preload_db):
    login_details = {"username": "test_admin", "password": "9409u8fgrejki0"}
    r = requests.post(login_url, data=login_details)
    assert(r.status_code == 200)
    tests.testutils.authJsonHeader = {"Authorization": "Bearer {}".format(json.loads(r.content)['access_token']), 'content-type': 'application/json'}
    tests.testutils.authHeader = {"Authorization": "Bearer {}".format(json.loads(r.content)['access_token'])}


def test_add_valid_user():
    r = add_user(payload)
    assert(r.status_code == 201)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']))
    global user_id
    user_id = int(json.loads(r.content)['id'])


def test_get_user_by_id():
    r = requests.get('{}/{}'.format(user_url, user_id), headers=tests.testutils.authHeader)
    assert(r.status_code == 200)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']) == user_id)
    assert(json.loads(r.content)['username'] == username)


def test_get_users():
    r = requests.get('{}s'.format(user_url),  headers=tests.testutils.authHeader)
    assert(r.status_code == 200)
    assert(is_json(r.content))
    users = models.User.query.all()
    assert(len(json.loads(r.content)['users']) == len(users))


def test_add_invalid_user_existing_username():
    r = add_user(payload)
    assert(r.status_code == 403)


def test_delete_other_user_as_coordinator():
    login_as("coordinator")
    r = requests.delete('{}/{}'.format(user_url, user_id), headers=tests.testutils.authHeader)
    assert(r.status_code == 401)


def test_delete_user():
    login_as("admin")
    r = requests.delete('{}/{}'.format(user_url, user_id), headers=tests.testutils.authHeader)
    assert(r.status_code == 202)
    assert(is_json(r.content))

    user = models.User.query.filter_by(id=user_id).first()
    assert user.flaggedForDeletion

    queue = models.DeleteFlags.query.filter_by(objectId=user_id, objectType=models.Objects.USER).first()
    assert int(queue.objectType) == int(models.Objects.USER)


def test_add_invalid_user_email():
    r = add_user(payload.update({"email": "invalidEmail"}))
    assert(r.status_code == 400)


def test_add_invalid_user_dob():
    r = add_user(payload.update({"dob": "221256"}))
    assert(r.status_code == 400)

# TODO more restricted fields

# TODO UserNameField and UserAddressField
