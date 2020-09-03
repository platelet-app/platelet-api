import uuid

import pytest
from app import app, db, models, guard, schemas
from tests.testutils import get_test_json, generate_name
import json

json_data = get_test_json()

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/bloodbike_test'
_client = app.test_client()

db.drop_all()
db.create_all()

db.session.commit()

api_url = "/api/v0.1/"

server_settings = models.ServerSettings.query.filter_by(id=1).first()
if server_settings:
    db.session.delete(server_settings)
    db.session.flush()

for patch in json_data['patches']:
    existing = None
    try:
        existing = models.Patch.query.filter_by(label=patch['label']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.flush()
    patch_model = models.Patch(**patch)

    db.session.add(patch_model)


for priority in json_data['priorities']:
    existing = None
    try:
        existing = models.Priority.query.filter_by(label=priority['label']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.flush()
    priority_model = models.Priority(**priority)

    db.session.add(priority_model)

for locale in json_data['locales']:
    existing = None
    try:
        existing = models.Locale.query.filter_by(label=locale['label']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.flush()
    locale_model = models.Locale(**locale)
    db.session.add(locale_model)

user_schema = schemas.UserSchema()
users_models = {}
for key in json_data['users']:
    user = user_schema.load(dict(**json_data['users'][key], password="somepass", username=generate_name(), display_name=generate_name()))
    users_models[key] = user
    db.session.add(user)


db.session.flush()

server_settings = models.ServerSettings(**json_data['server_settings'])
db.session.add(server_settings)
db.session.commit()

#db.session.remove()


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
                            ))
    print(user)
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


def rider_patch_mapper(rider):
    existing = None
    try:
        existing = models.User.query.filter_by(name=rider['username']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.flush()
    user_model = models.User(**rider)

    db.session.add(user_model)
    db.session.flush()
    return user_model.uuid


@pytest.fixture(scope="session")
def rider_patches_uuids():
    users = map(rider_patch_mapper, json_data['rider_patches'])
    db.session.commit()
    return set(users)


@pytest.fixture(scope="session")
def login_header_coordinator():
    schema = schemas.UserSchema()
    user = schema.load(dict(**json_data['users']['coordinator'],
                            username=generate_name(),
                            display_name=generate_name(),
                            password=guard.hash_password("somepass")
                            ))
    assert isinstance(user, models.User)
    db.session.add(user)
    db.session.commit()
    res = _client.post("{}login".format(api_url), data={"username": user.username, "password": "somepass"})
    assert res.status == "200 OK"
    token = json.loads(res.data)
    assert "access_token" in token
    header = {"Tab-Identification": "asdf", "Authorization": "Bearer {} ".format(token['access_token']), "content-type": "application/json"}
    yield header


@pytest.fixture(scope="session")
def login_header_rider():
    schema = schemas.UserSchema()
    user = schema.load(dict(**json_data['users']['rider'],
                            username=generate_name(),
                            display_name=generate_name(),
                            password=guard.hash_password("somepass")
                            ))
    assert isinstance(user, models.User)
    db.session.add(user)
    db.session.commit()
    res = _client.post("{}login".format(api_url), data={"username": user.username, "password": "somepass"})
    assert res.status == "200 OK"
    token = json.loads(res.data)
    assert "access_token" in token
    header = {"Authorization": "Bearer {} ".format(token['access_token']), "content-type": "application/json"}
    yield header


@pytest.fixture(scope="session")
def user_coordinator():
    res = dict(**json_data['users']['coordinator'], password="somepass", username=generate_name(), display_name=generate_name())
    return res


@pytest.fixture(scope="session")
def user_rider_uuid():
    user = models.User.query.filter_by(roles="rider").first()
    yield str(user.uuid)


@pytest.fixture(scope="session")
def user_coordinator_uuid():
    user = models.User.query.filter_by(roles="coordinator").first()
    yield str(user.uuid)


@pytest.fixture(scope="session")
def all_user_uuids():
    users = models.User.query.all()
    yield [str(i.uuid) for i in users]


@pytest.fixture(scope="session")
def coordinator_session_uuid():
    schema = schemas.UserSchema()
    user = schema.load(dict(**json_data['users']['coordinator'], password="somepass", username=generate_name(), display_name=generate_name()))
    db.session.add(user)
    db.session.commit()
    db.session.flush()
    session = models.Session(coordinator_uuid=user.uuid)
    db.session.add(session)
    db.session.commit()
    db.session.flush()
    yield str(session.uuid)


@pytest.fixture(scope="session")
def priorities_ids():
    yield [p.id for p in models.Priority.query.all()]


@pytest.fixture(scope="function")
def vehicle_obj():
    schema = schemas.VehicleSchema()
    vehicle = schema.load(dict(**json_data['vehicle_data'], name=generate_name()))
    db.session.add(vehicle)
    db.session.commit()
    db.session.flush()
    yield vehicle


@pytest.fixture(scope="function")
def comment_obj():
    # Make an author
    user_schema = schemas.UserSchema()
    author = user_schema.load(dict(**json_data['users']['rider'], display_name=generate_name(), username=generate_name()))
    db.session.add(author)
    # Make a parent object
    vehicle_schema = schemas.VehicleSchema()
    vehicle = vehicle_schema.load(dict(**json_data['vehicle_data'], name=generate_name()))
    db.session.add(vehicle)
    db.session.commit()
    db.session.flush()

    schema = schemas.CommentSchema()
    comment = schema.load(dict(**json_data['comment_data'], author_uuid=author.uuid, parent_uuid=vehicle.uuid))
    db.session.add(comment)
    db.session.commit()
    db.session.flush()
    yield comment


@pytest.fixture(scope="function")
def location_obj():
    schema = schemas.LocationSchema()
    location = schema.load(dict(**json_data['location_data'], name=generate_name()))
    db.session.add(location)
    db.session.commit()
    db.session.flush()
    yield location


@pytest.fixture(scope="session")
def task_objs_assigned():
    result = []
    for i in range(30):
        schema = schemas.TaskSchema()
        ts = schema.load(dict(**json_data['task_data']))
        try:
            ts.assigned_riders.append(users_models['rider'])
        except KeyError:
            raise KeyError("No rider is saved in the database for some reason.")
        assert ts
        db.session.add(ts)
        result.append(ts)

    db.session.commit()
    yield result


@pytest.fixture(scope="session")
def task_data():
    return json_data['task_data']


@pytest.fixture(scope="session")
def vehicle_data():
    data = json_data['vehicle_data']
    return data


@pytest.fixture(scope="session")
def vehicle_data_alternative():
    data = json_data['vehicle_data_alternative']
    return data


@pytest.fixture(scope="session")
def comment_data():
    data = json_data['comment_data']
    return data


@pytest.fixture(scope="session")
def comment_data_alternative():
    data = json_data['comment_data_alternative']
    return data


@pytest.fixture(scope="session")
def location_data():
    data = json_data['location_data']
    return data


@pytest.fixture(scope="session")
def location_data_alternative():
    data = json_data['location_data_alternative']
    return data


@pytest.fixture(scope="session")
def user_rider():
    res = dict(**json_data['users']['rider'], password="somepass", username=generate_name(), display_name=generate_name())
    return res

@pytest.fixture(scope="session")
def user_riders_different_patches():
    res = dict(**json_data['users']['rider'], password="somepass", username=generate_name(), display_name=generate_name())
    return res


def pytest_sessionfinish(session, exitstatus):
    db.drop_all()
