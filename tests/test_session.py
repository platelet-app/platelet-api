import json
from tests.testfunctions import is_json, login_url, session_url, user_url
from app import models
import requests

jwtKey = ""
authHeader = {}
authJsonHeader = {}
jsonHeader = {'content-type': 'application/json'}


# Util functions

def login_as(user_type):
    if user_type == "admin":
        login_details = {"username": "test_admin", "password": "9409u8fgrejki0"}
    elif user_type == "coordinator":
        login_details = {"username": "test_coordinator", "password": "9409u8fgrejki0"}
    elif user_type == "rider":
        login_details = {"username": "test_rider", "password": "9409u8fgrejki0"}
    else:
        raise ValueError("invalid user type")

    r = requests.post(login_url, data=login_details)
    assert(r.status_code == 200)
    global authJsonHeader
    authJsonHeader = {"Authorization": "Bearer {}".format(json.loads(r.content)['access_token']), 'content-type': 'application/json'}
    global authHeader
    authHeader = {"Authorization": "Bearer {}".format(json.loads(r.content)['access_token'])}

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

    r = requests.get('{}/{}'.format(user_url, username), headers=authHeader)
    assert(is_json(r.content))
    id = int(json.loads(r.content)['id'])
    assert(id)
    return id

def create_session(other_user_id = None):
    if other_user_id:
        data = {"user": other_user_id}
    else:
        data = ""

    return requests.post('{}s'.format(session_url), data=json.dumps(data), headers=authJsonHeader)

def create_session_success(other_user_id = None):
    r = create_session(other_user_id)
    assert(r.status_code == 201)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['user_id']))
    assert(int(json.loads(r.content)['id']))
    return int(json.loads(r.content)['id'])

def create_session_fail(other_user_id = None):
    r = create_session(other_user_id)
    assert(r.status_code == 401)

def delete_session(session_id):
    return requests.delete('{}/{}'.format(session_url, session_id), headers=authHeader)

def delete_session_success(session_id):
    r = delete_session(session_id)

    assert(r.status_code == 202)
    assert(is_json(r.content))
    session = models.Session.query.filter_by(id=session_id).first()
    assert session.flaggedForDeletion

    queue = models.DeleteFlags.query.filter_by(objectId=session_id, objectType=int(models.Objects.SESSION)).first()

    assert int(queue.objectType) == int(models.Objects.SESSION)

def delete_session_fail(session_id):
    r = delete_session(session_id)
    assert(r.status_code == 401)


# Test functions

def test_admin_create_session(preload_db):
    login_as("admin")
    global admin_session_id
    admin_session_id = create_session_success()

def test_coordinator_create_session(preload_db):
    login_as("coordinator")
    global coordinator_session_id
    coordinator_session_id = create_session_success()

def test_rider_create_session(preload_db):  # fails because of https://trello.com/c/pm9xGcvK/15-unauthorized-access-causes-server-error
    login_as("rider")
    create_session_fail()

def test_admin_create_session_other_user(preload_db):
    login_as("admin")
    create_session_success()

def test_coordinator_create_session_other_user(preload_db):
    login_as("coordinator")
    create_session_fail(find_user("admin"))  # fails because of https://trello.com/c/TsgIjdow/14-fix-user-get

def test_rider_create_session_other_user(preload_db):  # fails because of https://trello.com/c/pm9xGcvK/15-unauthorized-access-causes-server-error
    login_as("rider")
    create_session_fail(find_user("coordinator"))  # fails because of https://trello.com/c/TsgIjdow/14-fix-user-get

def test_rider_delete_session_other_user(preload_db):  # fails because of https://trello.com/c/pm9xGcvK/15-unauthorized-access-causes-server-error
    login_as("rider")
    delete_session_fail(coordinator_session_id)

def test_coordinator_delete_session_other_user(preload_db):
    login_as("coordinator")
    delete_session_fail(admin_session_id)

def test_coordinator_delete_session(preload_db):
    login_as("coordinator")
    delete_session_success(coordinator_session_id)

def test_admin_delete_session(preload_db):
    login_as("admin")
    delete_session_success(admin_session_id)

def test_admin_delete_session_other_user(preload_db):
    login_as("coordinator")
    other_user_session = create_session_success()
    login_as("admin")
    delete_session_success(other_user_session)
