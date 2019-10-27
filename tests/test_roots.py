import json
from tests.testutils import random_string, is_json, user_url, login_url, login_as, is_valid_uuid, print_response, attr_check, generate_name, get_object
import tests.testutils
from app import models, db, schemas, guard
from datetime import datetime

def test_ping(client, ):
    res = client.get('/api/v0.1/ping')
    assert res.status == "200 OK"


def test_login(client, user_coordinator):

    schema = schemas.UserSchema()
    user = schema.load(dict(user_coordinator,
                            username=generate_name(),
                            display_name=generate_name(),
                            password=guard.hash_password("somepass")
                            )).data
    assert isinstance(user, models.User)
    db.session.add(user)
    db.session.commit()
    res = client.post(login_url, data={"username": user.username, "password": "somepass"})
    assert res.status == "200 OK"
    token = json.loads(res.data)
    assert "access_token" in token
    db.session.delete(user)
    db.session.commit()
