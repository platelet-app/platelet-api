import json

import pytest

from tests.testutils import dict_check, location_url, is_valid_uuid, get_object, attr_check
from app import db
from app import models

LOCATION = models.Objects.LOCATION


@pytest.mark.parametrize("login_role", ["coordinator", "admin"])
def test_add_new_location(client, login_header, location_data):
    r = client.post("{}s".format(location_url),
                     data=json.dumps(location_data),
                     headers=login_header)
    new_uuid = r.json['uuid']
    obj = get_object(LOCATION, new_uuid)
    assert r.status_code == 201
    assert is_valid_uuid(new_uuid)
    check_data = location_data.copy()
    attr_check(check_data, obj, exclude=["timestamp", "links", "notes"])
    db.session.delete(obj)
    db.session.commit()


@pytest.mark.parametrize("login_role", ["coordinator", "admin"])
def test_update_location(client, login_header, location_data, location_data_alternative, location_obj):
    location_uuid = str(location_obj.uuid)
    check_data = location_data.copy()
    check_data['name'] = location_obj.name
    attr_check(check_data, location_obj, exclude=["timestamp", "links", "notes"])
    r = client.patch("{}/{}".format(location_url, location_uuid),
                     data=json.dumps(location_data_alternative),
                     headers=login_header)
    assert r.status_code == 200
    obj_updated = get_object(LOCATION, location_uuid)
    check_new_data = location_data_alternative.copy()
    check_new_data['name'] = obj_updated.name
    attr_check(check_new_data, obj_updated, exclude=["timestamp", "links", "notes"])


@pytest.mark.parametrize("login_role", ["rider", "coordinator", "admin"])
def test_get_location(client, login_header, location_data, location_obj):
    r = client.get("{}/{}".format(location_url, str(location_obj.uuid)),
                   headers=login_header)
    assert r.status_code == 200
    check_data = location_data.copy()
    check_data['name'] = location_obj.name
    dict_check(r.json, check_data, exclude=["links"])
