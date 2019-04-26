import json
from tests.testutils import random_string, is_json, user_url, login_url, login_as
import tests.testutils
from app import models
import requests

user_id = -1
username = "test_user"
address = {"address1": "123 fake street", "address2": "woopity complex",
           "town": "bristol", "county": "bristol", "postcode": "bs11 3ey",
           "country": "uk"}
payload = {"name": "Someone Person the 2nd",
           "password": "yepyepyep", "email": "asdf@asdf.com",
           "dob": "24/11/1987", "status": "active",
           "vehicle": "1", "patch": "north", "roles": "admin"}
payload.update({"username": username})
payload.update(address)


# Util functions

def add_user(data):
    return requests.post('{}s'.format(user_url), data=json.dumps(data), headers=tests.testutils.authJsonHeader)


# Test functions

# User and Users

def test_login(preload_db):
    login_details = {"username": "test_admin", "password": "9409u8fgrejki0"}
    r = requests.post(login_url, data=login_details)
    assert(r.status_code == 200)
    tests.testutils.authJsonHeader = {"Authorization": "Bearer {}".format(json.loads(r.content)['access_token']), 'content-type': 'application/json'}
    tests.testutils.authHeader = {"Authorization": "Bearer {}".format(json.loads(r.content)['access_token'])}


def test_add_valid_user():
    r = add_user(payload)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 201)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']))
    global user_id
    user_id = int(json.loads(r.content)['id'])


def test_get_user():
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
    print(json.loads(r.content)['message'])
    assert(r.status_code == 403)


def test_delete_other_user_as_coordinator():
    login_as("coordinator")
    r = requests.delete('{}/{}'.format(user_url, user_id), headers=tests.testutils.authHeader)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 403)


def test_delete_user():
    login_as("admin")
    r = requests.delete('{}/{}'.format(user_url, user_id), headers=tests.testutils.authHeader)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 202)
    assert(is_json(r.content))

    user = models.User.query.filter_by(id=user_id).first()
    assert user.flaggedForDeletion

    queue = models.DeleteFlags.query.filter_by(objectId=user_id, objectType=models.Objects.USER).first()
    assert int(queue.objectType) == int(models.Objects.USER)


def test_add_invalid_user_email():
    new_payload = payload.copy().update({"email": "invalidEmail"})
    r = add_user(new_payload)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 400)


def test_add_invalid_user_dob():
    new_payload = payload.copy().update({"dob": "221256"})
    r = add_user(new_payload)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 400)

# TODO more restricted fields


# UserNameField

def test_get_username():
    global username, payload
    username = "second_test_user"
    payload.update({"username": username})

    r = add_user(payload)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 201)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']))
    global user_id
    user_id = int(json.loads(r.content)['id'])

    r = requests.get('{}/{}/username'.format(user_url, user_id), headers=tests.testutils.authHeader)
    assert(r.status_code == 200)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']) == user_id)
    assert(json.loads(r.content)['username'] == username)


def test_change_username():
    new_username = "changed_username"
    data = {"username": new_username}
    r = requests.put('{}/{}/username'.format(user_url, user_id), data=json.dumps(data), headers=tests.testutils.authJsonHeader)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 200)

    r = requests.get('{}/{}/username'.format(user_url, user_id), headers=tests.testutils.authHeader)
    assert(r.status_code == 200)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']) == user_id)
    assert(json.loads(r.content)['username'] == new_username)


def test_change_id():
    new_id = 999
    data = {'id': new_id}
    r = requests.put('{}/{}/username'.format(user_url, user_id), data=json.dumps(data), headers=tests.testutils.authJsonHeader)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 400)


# UserAddressField

def test_get_address():
    r = requests.get('{}/{}/address'.format(user_url, user_id), headers=tests.testutils.authHeader)
    assert(r.status_code == 200)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']) == user_id)
    for key in address:
        if key == "postcode":
            assert(json.loads(r.content)[key] == address[key].upper())
        else:
            assert(json.loads(r.content)[key] == address[key])


def test_change_address():
    new_address = address.copy()
    new_address.update({"address1": "321 sill fake street"})
    r = requests.put('{}/{}/address'.format(user_url, user_id), data=json.dumps(new_address), headers=tests.testutils.authJsonHeader)
    print(json.loads(r.content)['message'])
    assert(r.status_code == 200)

    r = requests.get('{}/{}/address'.format(user_url, user_id), headers=tests.testutils.authHeader)
    assert(r.status_code == 200)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']) == user_id)
    for key in new_address:
        if key == "postcode":
            assert(json.loads(r.content)[key] == new_address[key].upper())
        else:
            assert(json.loads(r.content)[key] == new_address[key])
