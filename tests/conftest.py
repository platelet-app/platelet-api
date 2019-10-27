import os
import pytest
from config import basedir
from app import app, db, models, guard, schemas
from app.api.functions.userfunctions import is_username_present
import datetime
from tests.testutils import test_json
import json
from haikunator import Haikunator

def generate_name():
    haik = Haikunator()
    return haik.haikunate()

json_data = test_json()

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
def login_header():
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
def user_coordinator():
    res = dict(**json_data['users']['coordinator'], password=None, username=generate_name(), display_name=generate_name())
    return res


@pytest.fixture(scope="session")
def user_rider():
    return json_data['users'][2]
