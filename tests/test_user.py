import json
from tests.testutils import random_string, is_json, user_url, login_url, login_as, is_valid_uuid, print_response, attr_check, generate_name, get_object
import tests.testutils
from app import models, db
from datetime import datetime

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


# Test functions

# User and Users

def test_add_valid_user(client, user_coordinator, login_header_admin):
    r = client.post('{}s'.format(user_url), data=json.dumps(user_coordinator), headers=login_header_admin)
    print_response(r)
    assert(r.status_code == 201)

    data = json.loads(r.data)
    assert(is_valid_uuid(data['uuid']))
    del_user = get_object(USER, data['uuid'])
    assert isinstance(del_user, models.User)
    db.session.delete(del_user)
    db.session.commit()



def test_get_user(client, user_rider_uuid, login_header_admin):
    r = client.get('{}/{}'.format(user_url, user_rider_uuid), headers=login_header_admin)
    print_response(r)
    assert(r.status_code == 200)

    data = json.loads(r.data)
    user_model = get_object(USER, user_rider_uuid)

    #assert datetime(data['dob']) == user_model.dob

    attr_check(data, user_model, exclude=["password", "id", "dob", "links", "notes", "uuid"])


def test_get_users(client, all_user_uuids, login_header_admin):
    r = client.get('{}s'.format(user_url),  headers=login_header_admin)
    print_response(r)
    assert(r.status_code == 200)

    data = json.loads(r.data)

    users = models.User.query.all()

    for user in users:
        if str(user.uuid) in all_user_uuids:
            for i in data:
                if i['uuid'] == str(user.uuid):
                    attr_check(i, user, exclude=["password", "id", "dob", "links", "notes", "uuid", "email"])

    assert(len(data) == len(users))


def test_add_invalid_user_existing_username(client, login_header_admin, user_coordinator):
    r = client.post('{}s'.format(user_url), data=json.dumps(user_coordinator), headers=login_header_admin)
    assert(r.status_code == 201)
    user_coordinator['display_name'] = generate_name()
    r2 = client.post('{}s'.format(user_url), data=json.dumps(user_coordinator), headers=login_header_admin)
    assert(r2.status_code == 403)


def test_add_invalid_user_existing_displayname(client, login_header_admin, user_coordinator):
    r = client.post('{}s'.format(user_url), data=json.dumps(user_coordinator), headers=login_header_admin)
    assert(r.status_code == 201)
    user_coordinator['username'] = generate_name()
    r2 = client.post('{}s'.format(user_url), data=json.dumps(user_coordinator), headers=login_header_admin)
    assert(r2.status_code == 403)


def test_delete_other_user_as_coordinator(client, login_header_coordinator, user_rider_uuid):
    r = client.delete('{}/{}'.format(user_url, user_rider_uuid), headers=login_header_coordinator)
    print_response(r)
    assert(r.status_code == 403)


def test_delete_user(client, login_header_admin, user_rider_uuid):
    r = client.delete('{}/{}'.format(user_url, user_rider_uuid), headers=login_header_admin)
    print_response(r)
    assert(r.status_code == 202)

    user = get_object(USER, user_rider_uuid)
    assert user.flagged_for_deletion

    queue = models.DeleteFlags.query.filter_by(object_uuid=user_rider_uuid, object_type=USER).first()
    assert int(queue.object_type) == int(USER)


def test_add_invalid_user_email(client, user_rider, login_header_admin):
    new_payload = user_rider.copy().update({"email": "invalidEmail"})
    r = client.post('{}s'.format(user_url), data=json.dumps(new_payload), headers=login_header_admin)
    print_response(r)
    assert(r.status_code == 400)


def test_add_invalid_user_dob(client, user_rider, login_header_admin):
    new_payload = user_rider.copy().update({"dob": "221256"})
    r = client.post('{}s'.format(user_url), data=json.dumps(new_payload), headers=login_header_admin)
    print_response(r)
    assert(r.status_code == 400)

# TODO more restricted fields


# UserNameField

def test_get_username(client, user_rider_uuid, login_header_admin):
    user = get_object(USER, user_rider_uuid)


    r = client.get('{}/{}/username'.format(user_url, user.uuid), headers=login_header_admin)
    print_response(r)
    assert(r.status_code == 200)

    data = json.loads(r.data)
    assert(data['uuid'] == str(user.uuid))
    assert(data['username'] == user.username)


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

def test_get_address(client, login_header_admin, user_rider_uuid):
    user = get_object(USER, user_rider_uuid)
    r = client.get('{}/{}/address'.format(user_url, user_rider_uuid), headers=login_header_admin)
    print_response(r)
    assert(r.status_code == 200)

    data = json.loads(r.data)
    assert(data['uuid'] == user_rider_uuid)
    attr_check(data['address'], user.address)

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
