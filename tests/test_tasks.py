import json
from tests.testutils import is_json, is_valid_uuid, session_url, task_url, login_as, find_user, is_valid_uuid, print_response, whoami, delete_by_uuid, get_object, attr_check
from app import models

TASK = models.Objects.TASK


def test_add_new_task(client, login_header_coordinator):
    me = whoami(client, login_header_coordinator)
    r = client.post("{}s".format(session_url),
                    data=json.dumps({"user_uuid": me}),
                    headers=login_header_coordinator)
    print_response(r)
    assert r.status_code == 201
    session_uuid = json.loads(r.data)['uuid']
    r2 = client.post("{}s".format(task_url),
                     data=json.dumps({"session_id": session_uuid}),
                     headers=login_header_coordinator)
    print_response(r2)
    assert r2.status_code == 201
    assert is_valid_uuid(json.loads(r2.data)['uuid'])


def test_update_task(client, login_header_coordinator, task_data):
    me = whoami(client, login_header_coordinator)
    r = client.post("{}s".format(session_url),
                    data=json.dumps({"user_uuid": me}),
                    headers=login_header_coordinator)
    print_response(r)
    assert r.status_code == 201
    session_uuid = json.loads(r.data)['uuid']
    r2 = client.post("{}s".format(task_url),
                     data=json.dumps({"session_id": session_uuid}),
                     headers=login_header_coordinator)
    print_response(r2)
    assert r2.status_code == 201
    task_uuid = json.loads(r2.data)['uuid']
    assert is_valid_uuid(task_uuid)
    r3 = client.put("{}/{}".format(task_url, task_uuid),
                     data=json.dumps(task_data),
                     headers=login_header_coordinator)
    print_response(r3)
    assert r3.status_code == 200
    obj = get_object(TASK, task_uuid)
    attr_check(task_data, obj, exclude=["timestamp"])
