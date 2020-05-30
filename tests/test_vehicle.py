import json
from tests.testutils import dict_check, is_json, is_valid_uuid, session_url, vehicle_url, task_url, login_as, find_user, is_valid_uuid, print_response, whoami, delete_by_uuid, get_object, attr_check
from app import db
from app import models
from datetime import date, datetime

VEHICLE = models.Objects.VEHICLE

def convert_dates(data):
    data['date_of_manufacture'] = datetime.strptime(data['date_of_manufacture'], '%d/%m/%Y').date()
    data['date_of_registration'] = datetime.strptime(data['date_of_registration'], '%d/%m/%Y').date()
    return data

def test_add_new_vehicle(client, login_header_admin, vehicle_data):
    r = client.post("{}s".format(vehicle_url),
                     data=json.dumps(vehicle_data),
                     headers=login_header_admin)
    new_uuid = r.json['uuid']
    obj = get_object(VEHICLE, new_uuid)
    assert r.status_code == 201
    assert is_valid_uuid(new_uuid)
    check_data = vehicle_data.copy()
    check_data = convert_dates(check_data)
    attr_check(check_data, obj, exclude=["time_created", "time_modified", "links", "comments"])
    db.session.delete(obj)
    db.session.commit()


def test_update_new_vehicle(client, login_header_admin, vehicle_data, vehicle_data_alternative, vehicle_obj):
    check_data = vehicle_data.copy()
    check_data['name'] = vehicle_obj.name
    check_data = convert_dates(check_data)
    attr_check(check_data, vehicle_obj, exclude=["time_created", "time_modified", "links", "comments"])
    r = client.put("{}/{}".format(vehicle_url, vehicle_obj.uuid),
                     data=json.dumps(vehicle_data_alternative),
                     headers=login_header_admin)
    assert r.status_code == 200
    obj_updated = get_object(VEHICLE, vehicle_obj.uuid)
    check_new_data = vehicle_data_alternative.copy()
    check_new_data['name'] = obj_updated.name
    check_new_data = convert_dates(check_new_data)
    attr_check(check_new_data, obj_updated, exclude=["time_created", "time_modified", "timestamp", "links", "comments"])


def test_get_vehicle(client, login_header_coordinator, vehicle_data, vehicle_obj):
    r = client.get("{}/{}".format(vehicle_url, str(vehicle_obj.uuid)),
                   headers=login_header_coordinator)
    assert r.status_code == 200
    check_data = vehicle_data.copy()
    check_data['name'] = vehicle_obj.name
    dict_check(r.json, check_data, exclude=["time_created", "time_modified", "links", "comments"])


def test_delete_vehicle_admin(client, login_header_admin, vehicle_obj):
    r = client.delete("{}/{}".format(vehicle_url, str(vehicle_obj.uuid)),
                      headers=login_header_admin)
    assert r.status_code == 202
    db.session.flush()
    assert vehicle_obj.flagged_for_deletion
    r2 = client.get("{}/{}".format(vehicle_url, str(vehicle_obj.uuid)),
                    headers=login_header_admin)
    assert r2.status_code == 404


def test_delete_vehicle_others(client, login_header_coordinator, login_header_rider, vehicle_obj):
    r = client.delete("{}/{}".format(vehicle_url, str(vehicle_obj.uuid)),
                      headers=login_header_coordinator)
    assert r.status_code == 403
    db.session.flush()
    assert not vehicle_obj.flagged_for_deletion
    r2 = client.delete("{}/{}".format(vehicle_url, str(vehicle_obj.uuid)),
                      headers=login_header_rider)
    assert r2.status_code == 403
    db.session.flush()
    assert not vehicle_obj.flagged_for_deletion
