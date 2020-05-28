import json
from tests.testutils import dict_check, is_json, is_valid_uuid, location_url, vehicle_url, task_url, login_as, find_user, is_valid_uuid, print_response, whoami, delete_by_uuid, get_object, attr_check
from app import db
from app import models

LOCATION = models.Objects.LOCATION


def test_add_new_location(client, login_header_admin, location_data):
    r = client.post("{}s".format(location_url),
                     data=json.dumps(location_data),
                     headers=login_header_admin)
    new_uuid = r.json['uuid']
    obj = get_object(LOCATION, new_uuid)
    assert r.status_code == 201
    assert is_valid_uuid(new_uuid)
    check_data = location_data.copy()
    attr_check(check_data, obj, exclude=["timestamp", "links", "notes"])
    db.session.delete(obj)
    db.session.commit()


def test_update_location(client, login_header_admin, location_data, location_data_alternative, location_obj):
    check_data = location_data.copy()
    check_data['name'] = location_obj.name
    attr_check(check_data, location_obj, exclude=["timestamp", "links", "notes"])
    r = client.put("{}/{}".format(location_url, location_obj.uuid),
                     data=json.dumps(location_data_alternative),
                     headers=login_header_admin)
    assert r.status_code == 200
    obj_updated = get_object(LOCATION, location_obj.uuid)
    check_new_data = location_data_alternative.copy()
    check_new_data['name'] = obj_updated.name
    attr_check(check_new_data, obj_updated, exclude=["timestamp", "links", "notes"])


def test_get_location(client, login_header_coordinator, location_data, location_obj):
    r = client.get("{}/{}".format(location_url, str(location_obj.uuid)),
                   headers=login_header_coordinator)
    assert r.status_code == 200
    check_data = location_data.copy()
    check_data['name'] = location_obj.name
    dict_check(r.json, check_data, exclude=["links"])
