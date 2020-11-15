import json
from uuid import UUID

from tests.testutils import dict_check, is_json, is_valid_uuid, comment_url, session_url, vehicle_url, task_url, login_as, find_user, is_valid_uuid, print_response, whoami, delete_by_uuid, get_object, attr_check
from app import db
from app import models
from datetime import date, datetime

COMMENT = models.Objects.COMMENT


def test_add_new_comment(client, login_header_coordinator, comment_data, user_rider_uuid):
    data = comment_data.copy()
    data['parent_uuid'] = user_rider_uuid
    r = client.post("{}s".format(comment_url),
                    data=json.dumps(data),
                    headers=login_header_coordinator)
    new_uuid = r.json['uuid']
    obj = get_object(COMMENT, new_uuid)
    assert r.status_code == 201
    assert is_valid_uuid(new_uuid)
    check_data = data.copy()
    author_uuid = whoami(client, login_header_coordinator)
    author = get_object(models.Objects.USER, author_uuid)
    check_data['parent_uuid'] = UUID(user_rider_uuid)
    check_data['author_uuid'] = author.uuid
    attr_check(check_data, obj, exclude=["time_created", "time_modified", "links", "flagged_for_deletion", "parent_type", "author"])

    db.session.delete(obj)
    db.session.commit()


def test_update_comment(client, login_header_coordinator, comment_data, comment_data_alternative, user_rider_uuid):
    data = comment_data.copy()
    data['parent_uuid'] = user_rider_uuid
    r = client.post("{}s".format(comment_url),
                    data=json.dumps(data),
                    headers=login_header_coordinator)
    assert r.status_code == 201
    new_uuid = r.json['uuid']
    r2 = client.put("{}/{}".format(comment_url, new_uuid),
                   data=json.dumps(comment_data_alternative),
                   headers=login_header_coordinator)
    assert r2.status_code == 200
    obj_updated = get_object(COMMENT, new_uuid)
    assert obj_updated.body == comment_data_alternative['body']


def test_get_comment(client, login_header_coordinator, comment_data, comment_obj):
    r = client.get("{}/{}".format(comment_url, str(comment_obj.uuid)),
                   headers=login_header_coordinator)
    assert r.status_code == 200
    check_data = comment_data.copy()
    check_data['parent_uuid'] = comment_obj.parent_uuid
    check_data['author_uuid'] = comment_obj.author_uuid
    dict_check(r.json, check_data, exclude=["time_created", "time_modified"])


def test_delete_comment(client, login_header_rider, comment_data, user_coordinator_uuid):
    data = comment_data.copy()
    data['parent_uuid'] = user_coordinator_uuid
    r = client.post("{}s".format(comment_url),
                    data=json.dumps(data),
                    headers=login_header_rider)
    assert r.status_code == 201
    new_uuid = r.json['uuid']
    comment_obj = get_object(COMMENT, new_uuid)
    r2 = client.delete("{}/{}".format(comment_url, new_uuid),
                      headers=login_header_rider)
    assert r2.status_code == 202
    db.session.flush()
    assert comment_obj.deleted
    r3 = client.get("{}/{}".format(comment_url, str(comment_obj.uuid)),
                    headers=login_header_rider)
    assert r3.status_code == 404


def test_delete_comment_admin(client, login_header_admin, comment_obj):
    r = client.delete("{}/{}".format(comment_url, str(comment_obj.uuid)),
                   headers=login_header_admin)
    assert r.status_code == 202
    db.session.flush()
    assert comment_obj.deleted
    r2 = client.get("{}/{}".format(comment_url, str(comment_obj.uuid)),
                   headers=login_header_admin)
    assert r2.status_code == 404
