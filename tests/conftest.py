import os
import pytest
from config import basedir
from app import app, db, models, guard, schemas
from app.api.functions.userfunctions import is_username_present
import datetime
from tests.testutils import get_test_json, generate_name
import json

json_data = get_test_json()

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/bloodbike_test'
_client = app.test_client()

db.create_all()

db.session.commit()

api_url = "/api/v0.1/"

#db.session.remove()
#db.drop_all()

@pytest.fixture(scope="session")
def client():
    return _client


@pytest.fixture(scope="session")
def login_header_admin():
    schema = schemas.UserSchema()
    user = schema.load(dict(**json_data['users']['admin'],
                            username=generate_name(),
                            display_name=generate_name(),
                            password=guard.hash_password("somepass")
                            )).data
    assert isinstance(user, models.User)
    db.session.add(user)
    db.session.commit()
    res = _client.post("{}login".format(api_url), data={"username": user.username, "password": "somepass"})
    assert res.status == "200 OK"
    token = json.loads(res.data)
    assert "access_token" in token
    header = {"Authorization": "Bearer {} ".format(token['access_token']), "content-type": "application/json"}
    yield header
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope="session")
def login_header_coordinator():
    schema = schemas.UserSchema()
    user = schema.load(dict(**json_data['users']['coordinator'],
                            username=generate_name(),
                            display_name=generate_name(),
                            password=guard.hash_password("somepass")
                            )).data
    assert isinstance(user, models.User)
    db.session.add(user)
    db.session.commit()
    res = _client.post("{}login".format(api_url), data={"username": user.username, "password": "somepass"})
    assert res.status == "200 OK"
    token = json.loads(res.data)
    assert "access_token" in token
    header = {"Authorization": "Bearer {} ".format(token['access_token']), "content-type": "application/json"}
    yield header
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope="session")
def user_coordinator():
    res = dict(**json_data['users']['coordinator'], password="somepass", username=generate_name(), display_name=generate_name())
    return res


@pytest.fixture(scope="session")
def user_rider_uuid():
    schema = schemas.UserSchema()
    user = schema.load(dict(**json_data['users']['rider'], password="somepass", username=generate_name(), display_name=generate_name())).data
    db.session.add(user)
    db.session.commit()
    db.session.flush()
    yield str(user.uuid)
    db.session.delete(user)
    db.session.commit()

@pytest.fixture(scope="session")
def user_coordinator_uuid():
    schema = schemas.UserSchema()
    user = schema.load(dict(**json_data['users']['coordinator'], password="somepass", username=generate_name(), display_name=generate_name())).data
    db.session.add(user)
    db.session.commit()
    db.session.flush()
    yield str(user.uuid)
    db.session.delete(user)
    db.session.commit()

@pytest.fixture(scope="session")
def all_user_uuids():
    schema = schemas.UserSchema()
    users = []
    for key in json_data['users']:
        user = schema.load(dict(**json_data['users'][key], password="somepass", username=generate_name(), display_name=generate_name())).data
        db.session.add(user)
        db.session.commit()
        db.session.flush()
        users.append(user)

    yield [str(i.uuid) for i in users]
    for user in users:
        db.session.delete(user)
    db.session.commit()



@pytest.fixture(scope="session")
def user_rider():
    res = dict(**json_data['users']['rider'], password="somepass", username=generate_name(), display_name=generate_name())
    return res
