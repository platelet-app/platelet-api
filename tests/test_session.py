import json
from tests.testutils import is_json, session_url, login_as, find_user, is_valid_uuid, print_response
import tests.testutils
from app import models


# Util functions

def create_session(client, header, other_user_id=None):
    if other_user_id:
        data = {"user": str(other_user_id)}
    else:
        data = ""

    return client.post('{}s'.format(session_url), data=json.dumps(data), headers=header)


def create_session_success(client, header, other_user_id=None):
    r = create_session(client, header, other_user_id)
    print_response(r)
    assert(r.status_code == 201)
    data = json.loads(r.data)

    assert(is_valid_uuid(data['user_uuid']))
    assert(is_valid_uuid(data['uuid']))
    return data['uuid']


def create_session_fail(client, header, other_user_id=None):
    r = create_session(client, header, other_user_id)
    print_response(r)
    assert(r.status_code == 403)


def delete_session(client, header, session_id):
    return client.delete('{}/{}'.format(session_url, session_id), headers=header)


def delete_session_success(client, header, session_id):
    r = delete_session(client, header, session_id)
    print_response(r)
    assert(r.status_code == 202)

    session = models.Session.query.filter_by(uuid=session_id).first()
    assert session.flagged_for_deletion

    queue = models.DeleteFlags.query.filter_by(object_uuid=session_id, object_type=int(models.Objects.SESSION)).first()

    assert int(queue.object_type) == int(models.Objects.SESSION)


def delete_session_fail(client, header, session_id):
    r = delete_session(client, header, session_id)
    print_response(r)
    assert(r.status_code == 403)


# Test functions

def test_admin_create_session(client, login_header_admin):
    create_session_success(client, login_header_admin, )


def test_coordinator_create_session(client, login_header_coordinator):
    create_session_success(client, login_header_coordinator)


def test_rider_create_session(client, login_header_rider):
    create_session_fail(client, login_header_rider)


def test_admin_create_session_other_user(client, login_header_admin, user_coordinator_uuid):
    create_session_success(client, login_header_admin, other_user_id=user_coordinator_uuid)


def test_coordinator_create_session_other_user(client, login_header_coordinator, user_coordinator_uuid):
    create_session_fail(client, login_header_coordinator, other_user_id=user_coordinator_uuid)


def test_rider_create_session_other_user(client, login_header_rider, user_coordinator_uuid):
    create_session_fail(client, login_header_rider, user_coordinator_uuid)


def test_rider_delete_session_other_user(client, login_header_rider, coordinator_session_uuid):
    delete_session_fail(client, login_header_rider, coordinator_session_uuid)


def test_coordinator_delete_session_other_user(client, login_header_coordinator, coordinator_session_uuid):
    delete_session_fail(client, login_header_coordinator, coordinator_session_uuid)


def test_coordinator_delete_session(client, login_header_coordinator):
    session_uuid = create_session_success(client, login_header_coordinator)
    delete_session_success(client, login_header_coordinator, session_uuid)


def test_admin_delete_session_other_user(client, login_header_admin, coordinator_session_uuid):
    delete_session_success(client, login_header_admin, coordinator_session_uuid)
