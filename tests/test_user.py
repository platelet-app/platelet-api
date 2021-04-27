import json

import dateutil
import pytest

from tests.testutils import user_url, is_valid_uuid, attr_check, get_object, whoami
from app import models, db

USER = models.Objects.USER

user_id = -1
username = "test_user"
address = {"line1": "123 fake street", "line2": "woopity complex",
           "town": "bristol", "county": "bristol", "postcode": "bs113ey",
           "country": "uk"}
payload = {"name": "Someone Person the 2nd",
           "password": "yepyepyep", "email": "asdf@asdf.com",
           "dob": "24/11/1987", "status": "active",
           "patch": "north", "roles": "admin"}
payload.update({"username": username})
payload['address'] = address

exclude_attrs_list = ["password",
                      "id",
                      "dob",
                      "links",
                      "comments",
                      "assigned_vehicles",
                      "uuid",
                      "email",
                      "time_created",
                      "time_modified",
                      "roles",
                      "profile_picture_thumbnail_url",
                      "profile_picture_url"
                      ]


# Test functions

# User and Users

@pytest.mark.parametrize("login_role", ["admin"])
def test_add_valid_user(client, user_coordinator, login_header):
    r = client.post('{}s'.format(user_url), data=json.dumps(user_coordinator), headers=login_header)
    assert (r.status_code == 201)

    data = json.loads(r.data)
    assert (is_valid_uuid(data['uuid']))
    del_user = get_object(USER, data['uuid'])
    assert isinstance(del_user, models.User)
    db.session.delete(del_user)
    db.session.commit()


@pytest.mark.parametrize("login_role", ["admin", "rider", "coordinator"])
@pytest.mark.parametrize("user_role", ["admin"])
def test_get_user(client, user_obj, login_header):
    user_uuid = str(user_obj.uuid)
    r = client.get('{}/{}'.format(user_url, user_uuid), headers=login_header)
    assert (r.status_code == 200)

    data = json.loads(r.data)
    user_model = get_object(USER, user_uuid)

    attr_check(
        data,
        user_model,
        exclude=exclude_attrs_list
    )

    users_roles = user_model.roles.split(",")
    for role in data['roles']:
        assert role in users_roles


@pytest.mark.parametrize("login_role", ["admin", "coordinator", "rider"])
def test_get_users(client, all_user_uuids, login_header, user_objs):
    whoami_uuid = whoami(client, login_header)

    r = client.get('{}s'.format(user_url), headers=login_header)
    assert (r.status_code == 200)
    data = json.loads(r.data)
    user_uuids = [str(u.uuid) for u in user_objs]
    user_uuids.append(whoami_uuid)

    for user in data:
        assert user['uuid'] in user_uuids
        for i in user_objs:
            if i.uuid == str(user['uuid']):
                attr_check(
                    user,
                    i,
                    exclude=exclude_attrs_list)
                users_roles = user.roles.split(",")
                for role in i['roles']:
                    assert role in users_roles

    r2 = client.get('{}s?page={}'.format(user_url, 2), headers=login_header)
    assert (r.status_code == 200)
    data2 = json.loads(r2.data)

    for user in data2:
        assert user['uuid'] in user_uuids
        for i in user_objs:
            if i.uuid == str(user['uuid']):
                attr_check(
                    user,
                    i,
                    exclude=exclude_attrs_list)
                users_roles = user.roles.split(",")
                for role in i['roles']:
                    assert role in users_roles

    assert (len(data + data2) == len(user_uuids))


@pytest.mark.parametrize("login_role", ["admin", "rider", "coordinator"])
def test_get_users_role(client, all_user_uuids, login_header):
    r_coord = client.get('{}s?role={}'.format(user_url, "coordinator"), headers=login_header)
    assert (r_coord.status_code == 200)
    data = json.loads(r_coord.data)
    for u in data:
        assert "coordinator" in u['roles']
    r_rider = client.get('{}s?role={}'.format(user_url, "rider"), headers=login_header)
    assert (r_rider.status_code == 200)
    data = json.loads(r_rider.data)
    for u in data:
        assert "rider" in u['roles']
    r_admin = client.get('{}s?role={}'.format(user_url, "admin"), headers=login_header)
    assert (r_admin.status_code == 200)
    data = json.loads(r_admin.data)
    for u in data:
        assert "admin" in u['roles']


@pytest.mark.parametrize("users_order", ["newest", "oldest"])
@pytest.mark.parametrize("login_role", ["admin"])
def test_get_users_ordered(client, login_header, user_objs, users_order):
    r_latest = client.get('{}s?order={}'.format(user_url, users_order), headers=login_header)
    assert (r_latest.status_code == 200)
    data = json.loads(r_latest.data)
    assert len(data) == 20
    prev_user = None
    for i in data:
        print(i['time_created'])
        i['time_created'] = dateutil.parser.parse(i['time_created'])
    for user in data:
        if prev_user:
            if users_order == "newest":
                assert user['time_created'] < prev_user['time_created']
            else:
                assert user['time_created'] > prev_user['time_created']
        prev_user = user


@pytest.mark.parametrize("user_role", ["admin"])
@pytest.mark.parametrize("login_role", ["admin"])
def test_add_invalid_user_existing_username(client, login_header, user_obj):
    data = json.dumps({"username": user_obj.username})
    r2 = client.post('{}s'.format(user_url), data=data, headers=login_header)
    assert (r2.status_code == 400)


@pytest.mark.parametrize("user_role", ["admin"])
@pytest.mark.parametrize("login_role", ["admin"])
def test_add_invalid_user_existing_display_name(client, login_header, user_obj):
    data = json.dumps({"display_name": user_obj.display_name})
    r = client.post('{}s'.format(user_url), data=data, headers=login_header)
    assert (r.status_code == 400)


@pytest.mark.parametrize("user_role", ["rider"])
@pytest.mark.parametrize("login_role", ["rider", "coordinator"])
def test_delete_user_as_other(client, login_header, user_obj):
    user_uuid = str(user_obj.uuid)
    r = client.delete('{}/{}'.format(user_url, user_uuid), headers=login_header)
    assert (r.status_code == 403)


@pytest.mark.parametrize("user_role", ["rider"])
@pytest.mark.parametrize("login_role", ["admin"])
def test_delete_user(client, login_header, user_obj):
    user_uuid = str(user_obj.uuid)
    r = client.delete('{}/{}'.format(user_url, user_uuid), headers=login_header)
    assert (r.status_code == 202)

    user = get_object(USER, user_uuid, with_deleted=True)
    assert user.deleted


@pytest.mark.parametrize("login_role", ["admin"])
def test_add_invalid_user_email(client, user_rider, login_header):
    new_payload = user_rider.copy().update({"email": "invalidEmail"})
    r = client.post('{}s'.format(user_url), data=json.dumps(new_payload), headers=login_header)
    assert (r.status_code == 400)


@pytest.mark.parametrize("login_role", ["admin"])
def test_add_invalid_user_dob(client, user_rider, login_header):
    new_payload = user_rider.copy().update({"dob": "221256"})
    r = client.post('{}s'.format(user_url), data=json.dumps(new_payload), headers=login_header)
    assert (r.status_code == 400)

# TODO more restricted fields


# UserNameField

# def test_get_username(client, user_rider_uuid, login_header_admin):
#    user = get_object(USER, user_rider_uuid)
#
#
#    r = client.get('{}/{}/username'.format(user_url, user.uuid), headers=login_header_admin)
#    print_response(r)
#    assert(r.status_code == 200)
#
#    data = json.loads(r.data)
#    assert(data['uuid'] == str(user.uuid))
#    assert(data['username'] == user.username)


# def test_change_username(client):
#     new_username = "changed_username"
#     data = {"username": new_username}
#     r = client.put('{}/{}/username'.format(user_url, user_id), data=json.dumps(data), headers=tests.testutils.authJsonHeader)
#     print_response(r)
#     assert(r.status_code == 200)
#
#     r = client.get('{}/{}/username'.format(user_url, user_id), headers=tests.testutils.authHeader)
#     print_response(r)
#     assert(r.status_code == 200)
#
#     data = json.loads(r.data)
#     assert(data['uuid'] == user_id)
#     assert(data['username'] == new_username)


# def test_change_id(client):
#     new_id = 999
#     payload = {'id': new_id}
#     r = client.put('{}/{}/username'.format(user_url, user_id), data=json.dumps(payload), headers=tests.testutils.authJsonHeader)
#     print_response(r)
#     assert(r.status_code == 200)


# UserAddressField

# def test_get_address(client, login_header_admin, user_rider_uuid):
#    user = get_object(USER, user_rider_uuid)
#    r = client.get('{}/{}/address'.format(user_url, user_rider_uuid), headers=login_header_admin)
#    print_response(r)
#    assert(r.status_code == 200)
#
#    data = json.loads(r.data)
#    assert(data['uuid'] == user_rider_uuid)
#    attr_check(data['address'], user.address)

# def test_change_address(client):
#     new_address = address.copy()
#     new_address.update({"line1": "321 sill fake street"})
#     payload = {'address': new_address}
#     r = client.put('{}/{}/address'.format(user_url, user_id), data=json.dumps(payload), headers=tests.testutils.authJsonHeader)
#     print_response(r)
#     assert(r.status_code == 200)
#
#     r = client.get('{}/{}/address'.format(user_url, user_id), headers=tests.testutils.authHeader)
#     print_response(r)
#     assert(r.status_code == 200)
#
#     data = json.loads(r.data)
#     assert(data['uuid'] == user_id)
#     resulting_address = data['address']
#     for key in new_address:
#         if key == "postcode":
#             assert(resulting_address[key] == new_address[key].upper())
#         else:
#             assert(resulting_address[key] == new_address[key])
