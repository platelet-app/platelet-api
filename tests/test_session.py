import json
from tests.testutils import is_json, session_url, login_as, find_user, is_valid_uuid, print_response
import tests.testutils
from app import models


# Util functions

def create_session(client, other_user_id=None):
    if other_user_id:
        data = {"user": str(other_user_id)}
    else:
        data = ""

    return client.post('{}s'.format(session_url), data=json.dumps(data), headers=tests.testutils.authJsonHeader)


def create_session_success(client, other_user_id=None):
    r = create_session(client, other_user_id)
    print_response(r)
    assert(r.status_code == 201)
    data = json.loads(r.data)


    assert(is_valid_uuid(data['user_uuid']))
    assert(is_valid_uuid(data['uuid']))
    return data['uuid']


def create_session_fail(client, other_user_id=None):
    r = create_session(client, other_user_id)
    print_response(r)
    assert(r.status_code == 403)


def delete_session(client, session_id):
    return client.delete('{}/{}'.format(session_url, session_id), headers=tests.testutils.authHeader)


def delete_session_success(client, session_id):
    r = delete_session(client, session_id)
    print_response(r)
    assert(r.status_code == 202)

    session = models.Session.query.filter_by(uuid=session_id).first()
    assert session.flagged_for_deletion

    queue = models.DeleteFlags.query.filter_by(object_uuid=session_id, object_type=int(models.Objects.SESSION)).first()

    assert int(queue.object_type) == int(models.Objects.SESSION)


def delete_session_fail(client, session_id):
    r = delete_session(client, session_id)
    print_response(r)
    assert(r.status_code == 403)


# Test functions

def test_admin_create_session(client):
    login_as(client, "admin")
    global admin_session_id
    admin_session_id = create_session_success(client)


def test_coordinator_create_session(client):
    login_as(client, "coordinator")
    global coordinator_session_id
    coordinator_session_id = create_session_success(client)


def test_rider_create_session(client):
    login_as(client, "rider")
    create_session_fail(client)


def test_admin_create_session_other_user(client):
    login_as(client, "admin")
    create_session_success(client)


def test_coordinator_create_session_other_user(client):
    login_as(client, "coordinator")
    create_session_fail(client, find_user("admin"))


def test_rider_create_session_other_user(client):
    login_as(client, "rider")
    create_session_fail(client, find_user("coordinator"))


def test_rider_delete_session_other_user(client):
    login_as(client, "rider")
    delete_session_fail(client, coordinator_session_id)


def test_coordinator_delete_session_other_user(client):
    login_as(client, "coordinator")
    delete_session_fail(client, admin_session_id)


def test_coordinator_delete_session(client):
    login_as(client, "coordinator")
    delete_session_success(client, coordinator_session_id)


def test_admin_delete_session(client):
    login_as(client, "admin")
    delete_session_success(client, admin_session_id)


def test_admin_delete_session_other_user(client):
    login_as(client, "coordinator")
    other_user_session = create_session_success(client)
    login_as(client, "admin")
    delete_session_success(client, other_user_session)
