import json
from tests.testutils import is_json, session_url, login_as, find_user, is_valid_uuid
import tests.testutils
from app import models
import requests


# Util functions

def create_session(other_user_id = None):
    if other_user_id:
        data = {"user": str(other_user_id)}
    else:
        data = ""

    return requests.post('{}s'.format(session_url), data=json.dumps(data), headers=tests.testutils.authJsonHeader)


def create_session_success(other_user_id=None):
    r = create_session(other_user_id)
    assert(r.status_code == 201)
    assert(is_json(r.content))
    assert(is_valid_uuid(json.loads(r.content)['user_uuid']))
    assert(is_valid_uuid(json.loads(r.content)['uuid']))
    return json.loads(r.content)['uuid']


def create_session_fail(other_user_id=None):
    r = create_session(other_user_id)
    assert(r.status_code == 403)


def delete_session(session_id):
    return requests.delete('{}/{}'.format(session_url, session_id), headers=tests.testutils.authHeader)


def delete_session_success(session_id):
    r = delete_session(session_id)

    assert(r.status_code == 202)
    assert(is_json(r.content))
    session = models.Session.query.filter_by(uuid=session_id).first()
    assert session.flagged_for_deletion

    queue = models.DeleteFlags.query.filter_by(object_uuid=session_id, object_type=int(models.Objects.SESSION)).first()

    assert int(queue.object_type) == int(models.Objects.SESSION)


def delete_session_fail(session_id):
    r = delete_session(session_id)
    assert(r.status_code == 403)


# Test functions

def test_admin_create_session(preload_db):
    login_as("admin")
    global admin_session_id
    admin_session_id = create_session_success()


def test_coordinator_create_session(preload_db):
    login_as("coordinator")
    global coordinator_session_id
    coordinator_session_id = create_session_success()


def test_rider_create_session(preload_db):
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
