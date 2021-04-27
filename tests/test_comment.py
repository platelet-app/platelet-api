import json

import pytest

from tests.testutils import dict_check, comment_url, is_valid_uuid, whoami, get_object, attr_check
from app import models

COMMENT = models.Objects.COMMENT


@pytest.mark.parametrize("login_role", ["rider", "coordinator", "admin"])
@pytest.mark.parametrize("parent_type", ["vehicle", "user", "location", "task"])
def test_add_new_comment(client, login_header, comment_data, comment_parent_obj):
    data = comment_data.copy()
    check_data = data.copy()
    data['parent_uuid'] = str(comment_parent_obj.uuid)
    check_data['parent_uuid'] = comment_parent_obj.uuid

    r = client.post("{}s".format(comment_url),
                    data=json.dumps(data),
                    headers=login_header)
    new_uuid = r.json['uuid']
    obj = get_object(COMMENT, new_uuid)
    assert r.status_code == 201
    assert is_valid_uuid(new_uuid)
    author_uuid = whoami(client, login_header)
    author = get_object(models.Objects.USER, author_uuid)
    check_data['author_uuid'] = author.uuid
    attr_check(check_data, obj, exclude=["time_created", "time_modified", "links", "deleted", "parent_type", "author"])


@pytest.mark.parametrize("login_role", ["rider", "coordinator", "admin"])
@pytest.mark.parametrize("parent_type", ["vehicle", "user", "location", "task"])
def test_update_comment(client, login_header, comment_data, comment_data_alternative, comment_parent_obj):
    data = comment_data.copy()
    data['parent_uuid'] = str(comment_parent_obj.uuid)
    r = client.post("{}s".format(comment_url),
                    data=json.dumps(data),
                    headers=login_header)
    assert r.status_code == 201
    new_uuid = r.json['uuid']
    r2 = client.patch("{}/{}".format(comment_url, new_uuid),
                   data=json.dumps(comment_data_alternative),
                   headers=login_header)
    assert r2.status_code == 200
    obj_updated = get_object(COMMENT, new_uuid)
    assert obj_updated.body == comment_data_alternative['body']


@pytest.mark.parametrize("login_role", ["rider", "coordinator", "admin"])
@pytest.mark.parametrize("parent_type", ["vehicle", "user", "location", "task"])
def test_get_comment(client, login_header, comment_data, comment_obj):
    r = client.get("{}/{}".format(comment_url, str(comment_obj.uuid)),
                   headers=login_header)
    assert r.status_code == 200
    check_data = comment_data.copy()
    check_data['parent_uuid'] = comment_obj.parent_uuid
    check_data['author_uuid'] = comment_obj.author_uuid
    dict_check(r.json, check_data, exclude=["time_created", "time_modified"])


@pytest.mark.parametrize("login_role", ["rider", "coordinator", "admin"])
@pytest.mark.parametrize("parent_type", ["vehicle", "user", "location", "task"])
def test_delete_comment(client, login_header, comment_data, comment_parent_obj):
    data = comment_data.copy()
    data['parent_uuid'] = str(comment_parent_obj.uuid)
    r = client.post("{}s".format(comment_url),
                    data=json.dumps(data),
                    headers=login_header)
    assert r.status_code == 201
    new_uuid = r.json['uuid']
    r2 = client.delete("{}/{}".format(comment_url, new_uuid),
                       headers=login_header)
    assert r2.status_code == 202
    comment_obj = get_object(COMMENT, new_uuid, with_deleted=True)
    assert comment_obj.deleted
    r3 = client.get("{}/{}".format(comment_url, str(comment_obj.uuid)),
                    headers=login_header)
    assert r3.status_code == 404


@pytest.mark.parametrize("login_role", ["admin"])
@pytest.mark.parametrize("parent_type", ["vehicle", "user", "location", "task"])
def test_delete_any_comment_admin(client, login_header, comment_obj):
    comment_uuid = str(comment_obj.uuid)
    r = client.delete("{}/{}".format(comment_url, comment_uuid),
                   headers=login_header)
    assert r.status_code == 202
    comment_obj = get_object(COMMENT, comment_uuid, with_deleted=True)
    assert comment_obj.deleted
    r2 = client.get("{}/{}".format(comment_url, comment_uuid),
                   headers=login_header)
    assert r2.status_code == 404
