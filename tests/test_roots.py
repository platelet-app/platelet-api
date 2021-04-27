import json
from tests.testutils import login_url, attr_check, generate_name
from app import models, db, schemas, guard

def test_ping(client):
    res = client.get('/api/v0.1/ping')
    assert res.status == "200 OK"

def test_login(client, user_coordinator):
    schema = schemas.UserSchema()
    user = schema.load(dict(user_coordinator,
                            username=generate_name(),
                            display_name=generate_name(),
                            password=guard.hash_password("somepass")
                            ))
    assert isinstance(user, models.User)
    db.session.add(user)
    db.session.commit()
    res = client.post(login_url, data={"username": user.username, "password": "somepass"})
    assert res.status == "200 OK"
    token = json.loads(res.data)
    assert "access_token" in token
    db.session.delete(user)
    db.session.commit()


def test_server_settings(client):
    res = client.get("/api/v0.1/server_settings")
    settings = models.ServerSettings.query.filter_by(id=1).first()
    attr_check(json.loads(res.data), settings)
