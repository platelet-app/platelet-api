import json

import pytest

from tests.testutils import is_json, is_valid_uuid, session_url, task_url, login_as, find_user, is_valid_uuid, print_response, whoami, delete_by_uuid, get_object, attr_check
from app import models

TASK = models.Objects.TASK


def test_get_all_tasks(client, login_header_coordinator, user_rider_uuid, task_objs_assigned):
    r = client.get("{}s".format(task_url, 1),
                   headers=login_header_coordinator)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    r = client.get("{}s".format(task_url),
                   headers=login_header_coordinator)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20


@pytest.mark.parametrize("user_role", ["rider", "coordinator"])
def test_get_assigned_tasks(client, login_header_coordinator, task_objs_assigned, user_role):
    assigned_user_uuid = str(task_objs_assigned[0].assigned_riders[0].uuid) if user_role == "rider" else str(task_objs_assigned[0].assigned_coordinators[0].uuid)
    r = client.get("{}s/{}?page={}&role={}".format(task_url, assigned_user_uuid, 1, user_role),
                    headers=login_header_coordinator,)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    # test with no page given
    r = client.get("{}s/{}?role={}".format(task_url, assigned_user_uuid, user_role),
                   headers=login_header_coordinator)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    # test page 2
    r = client.get("{}s/{}?page={}&role={}".format(task_url, assigned_user_uuid, 2, user_role),
                   headers=login_header_coordinator,)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 10


def test_add_new_task(client, login_header_coordinator):
    r2 = client.post("{}s".format(task_url),
                     data=json.dumps({}),
                     headers=login_header_coordinator)
    print_response(r2)
    assert r2.status_code == 201
    assert is_valid_uuid(json.loads(r2.data)['uuid'])


def test_update_task(client, login_header_coordinator, task_data):
    r2 = client.post("{}s".format(task_url),
                     data=json.dumps({}),
                     headers=login_header_coordinator)
    print_response(r2)
    assert r2.status_code == 201
    task_uuid = json.loads(r2.data)['uuid']
    assert is_valid_uuid(task_uuid)
    r3 = client.patch("{}/{}".format(task_url, task_uuid),
                     data=json.dumps(task_data),
                     headers=login_header_coordinator)
    print_response(r3)
    assert r3.status_code == 200
    obj = get_object(TASK, task_uuid)
    attr_check(task_data, obj, exclude=["timestamp"])
