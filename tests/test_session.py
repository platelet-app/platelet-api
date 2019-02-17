import json
from tests.testfunctions import random_string, is_json
from app import models
import requests

user_id = -1
session_id = -1
jwtKey = ""
authHeader = {}
authJsonHeader = {}
jsonHeader = {'content-type': 'application/json'}

url = 'http://localhost:5000/api/v0.1/session'
loginUrl = 'http://localhost:5000/api/v0.1/login'


def test_login():
    login_details = {"username": "coordinator", "password": "9409u8fgrejki0"}
    r = requests.post(loginUrl, data=login_details)
    assert(r.status_code == 200)
    global authJsonHeader
    authJsonHeader = {"Authorization": "Bearer {}".format(json.loads(r.content)['access_token']), 'content-type': 'application/json'}
    global authHeader
    authHeader = {"Authorization": "Bearer {}".format(json.loads(r.content)['access_token'])}


def test_create_session():
    r = requests.post('{}s'.format(url), data=json.dumps(""), headers=authJsonHeader)
    assert(r.status_code == 201)
    assert(is_json(r.content))
    assert(int(json.loads(r.content)['user_id']))
    assert(int(json.loads(r.content)['id']))
    global session_id
    session_id = int(json.loads(r.content)['id'])


def test_delete_session():
    if session_id > 0:
        r = requests.delete('{}/{}'.format(url, session_id), headers=authHeader)
        assert(r.status_code == 202)
        assert(is_json(r.content))
        session = models.Session.query.filter_by(id=session_id).first()
        assert session.flaggedForDeletion

        queue = models.DeleteFlags.query.filter_by(objectId=session_id, objectType=int(models.Objects.SESSION)).first()

        assert int(queue.objectType) == int(models.Objects.SESSION)
