import json
from tests.testfunctions import random_string, is_json
from app import db, models

user_id = -1


import requests

url = 'http://localhost:5000/api/v0.1/user'

payload = {"name": "Someone Person the 2nd",
           "username": "{}".format(random_string()),
           "password": "yepyepyep", "email": "asdf@asdf.com",
           "dob": "24/11/1987", "status": "active",
           "vehicle": "1", "patch": "north",
           "address1": "123 fake street", "address2": "woopity complex",
           "town": "bristol", "county": "bristol", "postcode": "bs11 3ey",
           "country": "uk"}


def test_addUser():
    r = requests.post('{}s'.format(url), data=payload)
    assert(r.status_code == 201)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['id']))
    global user_id
    user_id = int(json.loads(r.content)['id'])


def test_getUsers():
    r = requests.get('{}s'.format(url))
    assert(r.status_code == 200)
    assert(is_json(r.content))
    users = models.User.query.all()
    assert(len(json.loads(r.content)['users']) == len(users))


def test_deleteUser():
    if user_id > 0:
        r = requests.delete('{}/{}'.format(url, user_id), data=payload)
        assert(r.status_code == 202)
        assert(is_json(r.content))


        user = models.User.query.filter_by(id=user_id).first()
        assert (user.flaggedForDeletion == True)

        queue = models.DeleteFlags.query.filter_by(objectId=user_id).first()

        assert queue.objectType == models.Objects.USER
