import json

import pytest

from tests.testutils import task_url, is_valid_uuid, print_response, get_object, attr_check
from app import models

TASK = models.Objects.TASK


@pytest.mark.parametrize("login_role", ["coordinator"])
def test_post_relay(client, login_header, task_obj):
    r = client.post("{}s".format(task_url),
                     data=json.dumps({
                         "relay_previous_uuid": str(task_obj.uuid),
                         "parent_id": task_obj.parent_id
                     }),
                     headers=login_header)
    print_response(r)
    assert r.status_code == 201
    data = json.loads(r.data)
    assert is_valid_uuid(data['uuid'])
    new_task = get_object(TASK, data['uuid'])
    assert new_task.relay_previous_uuid == task_obj.uuid


@pytest.mark.parametrize("login_role", ["coordinator"])
@pytest.mark.parametrize("user_role", ["coordinator"])
@pytest.mark.parametrize("task_status", ["new"])
def test_get_all_tasks(client, login_header, task_objs_assigned):
    r = client.get("{}s".format(task_url, 1),
                   headers=login_header)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    r = client.get("{}s".format(task_url),
                   headers=login_header)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20


@pytest.mark.parametrize("login_role", ["coordinator"])
@pytest.mark.parametrize("user_role", ["rider", "coordinator"])
@pytest.mark.parametrize("task_status", ["new"])
def test_get_assigned_tasks(client, login_header, task_objs_assigned, user_role):
    assigned_user_uuid = str(task_objs_assigned[0].assigned_riders[0].uuid) if user_role == "rider" else str(task_objs_assigned[0].assigned_coordinators[0].uuid)
    r = client.get("{}s/{}?page={}&role={}".format(task_url, assigned_user_uuid, 1, user_role),
                    headers=login_header,)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    # test with no page given
    r = client.get("{}s/{}?role={}".format(task_url, assigned_user_uuid, user_role),
                   headers=login_header)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    # test page 2
    r = client.get("{}s/{}?page={}&role={}".format(task_url, assigned_user_uuid, 2, user_role),
                   headers=login_header,)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 10


@pytest.mark.parametrize("login_role", ["coordinator"])
@pytest.mark.parametrize("user_role", ["coordinator"])
@pytest.mark.parametrize("task_status", ["new"])
def test_get_assigned_tasks_by_new_coordinator(client, login_header, task_objs_assigned, user_role):
    assigned_user_uuid = str(task_objs_assigned[0].assigned_coordinators[0].uuid)
    r = client.get("{}s/{}?page={}&role={}&status={}".format(task_url, assigned_user_uuid, 1, user_role, "new"),
                   headers=login_header)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    # test with no page given
    r = client.get("{}s/{}?role={}&status={}".format(task_url, assigned_user_uuid, user_role, "new"),
                   headers=login_header)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    # test page 2
    r = client.get("{}s/{}?page={}&role={}&status={}".format(task_url, assigned_user_uuid, 2, user_role, "new"),
                   headers=login_header)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 10


@pytest.mark.parametrize("login_role", ["coordinator"])
@pytest.mark.parametrize("user_role", ["coordinator"])
@pytest.mark.parametrize("task_status", ["new", "active", "picked_up", "delivered", "cancelled", "rejected"])
def test_get_assigned_tasks_by_status_coordinator(client, login_header, task_objs_assigned, user_role, task_status):
    assigned_user_uuid = str(task_objs_assigned[0].assigned_coordinators[0].uuid)
    r = client.get("{}s/{}?page={}&role={}&status={}".format(task_url, assigned_user_uuid, 1, user_role, task_status),
                   headers=login_header)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    # test with no page given
    r = client.get("{}s/{}?role={}".format(task_url, assigned_user_uuid, user_role),
                   headers=login_header)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 20
    # test page 2
    r = client.get("{}s/{}?page={}&role={}".format(task_url, assigned_user_uuid, 2, user_role),
                   headers=login_header,)
    assert r.status_code == 200
    result = json.loads(r.data)
    assert len(result) == 10


@pytest.mark.parametrize("login_role", ["coordinator"])
def test_post_task(client, login_header):
    r2 = client.post("{}s".format(task_url),
                     data=json.dumps({}),
                     headers=login_header)
    print_response(r2)
    assert r2.status_code == 201
    assert is_valid_uuid(json.loads(r2.data)['uuid'])


@pytest.mark.parametrize("login_role", ["coordinator"])
def test_update_task(client, login_header, task_data, task_obj, login_role):
    task_uuid = str(task_obj.uuid)
    r3 = client.patch("{}/{}".format(task_url, task_uuid),
                     data=json.dumps(task_data),
                     headers=login_header)
    print_response(r3)
    assert r3.status_code == 200
    obj = get_object(TASK, task_uuid)
    attr_check(task_data, obj, exclude=["timestamp"])


@pytest.mark.parametrize("login_role", ["coordinator"])
@pytest.mark.parametrize("user_role", ["rider", "coordinator"])
def test_task_assignment_get(client, login_header, task_obj_assigned, user_role):
    assignee_uuid = str(task_obj_assigned.assigned_riders[0].uuid) if user_role == "rider" else str(task_obj_assigned.assigned_coordinators[0].uuid)
    r = client.get("{}/{}/assigned_users?role={}".format(task_url, task_obj_assigned.uuid, user_role),
                   headers=login_header)
    assert r.status_code == 200
    user_uuid = json.loads(r.data)[0]['uuid']
    assert user_uuid == assignee_uuid


@pytest.mark.parametrize("login_role", ["coordinator"])
@pytest.mark.parametrize("user_role", ["rider", "coordinator"])
def test_task_assignment_put(client, login_header, task_obj, user_obj, user_role):
    assignee_uuid = str(user_obj.uuid)
    task_uuid = str(task_obj.uuid)
    data = {"user_uuid": assignee_uuid}
    r = client.put("{}/{}/assigned_users?role={}".format(task_url, task_uuid, user_role),
                   data=json.dumps(data),
                   headers=login_header)
    assert r.status_code == 200
    r = client.get("{}/{}/assigned_users?role={}".format(task_url, task_uuid, user_role),
                   headers=login_header)
    assert r.status_code == 200
    user_uuid = json.loads(r.data)[0]['uuid']
    assert user_uuid == assignee_uuid


@pytest.mark.parametrize("destination_location", ["pickup", "delivery"])
@pytest.mark.parametrize("login_role", ["coordinator"])
def test_task_assign_saved_location(client, login_header, destination_location, location_obj, task_obj):
    task_uuid = str(task_obj.uuid)
    r = client.put(
        "{}/{}/destinations?destination={}".format(task_url, task_uuid, destination_location),
        headers=login_header,
        data=json.dumps({"location_uuid": str(location_obj.uuid)}))
    assert r.status_code == 200
    obj = get_object(TASK, task_uuid)
    if destination_location == "pickup":
        assert obj.pickup_address_id == location_obj.address_id
        assert obj.saved_location_pickup_uuid == location_obj.uuid
    else:
        assert obj.dropoff_address_id == location_obj.address_id
        assert obj.saved_location_dropoff_uuid == location_obj.uuid


@pytest.mark.parametrize("destination_location", ["pickup", "delivery", "both"])
@pytest.mark.parametrize("login_role", ["coordinator"])
def test_get_task_destinations(client, login_header, location_obj, task_obj_addressed, destination_location):
    task_uuid = str(task_obj_addressed.uuid)
    r = client.get(
        "{}/{}/destinations?destination={}".format(task_url, task_uuid, destination_location),
        headers=login_header
    )
    assert r.status_code == 200
    result = json.loads(r.data)
    print(result)
    if destination_location == "pickup":
        attr_check(result, task_obj_addressed.pickup_address)
    elif destination_location == "delivery":
        attr_check(result, task_obj_addressed.dropoff_address)
    else:
        attr_check(result["pickup"], task_obj_addressed.pickup_address)
        attr_check(result["delivery"], task_obj_addressed.dropoff_address)

