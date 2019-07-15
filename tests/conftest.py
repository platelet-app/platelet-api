import os
import pytest
from config import basedir
from app import app, db, models, guard
from app.api.functions.userfunctions import is_username_present
import datetime


@pytest.fixture(scope="session")
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/bloodbike_test'
    client = app.test_client()

    db.create_all()

    date = datetime.datetime.strptime('24/01/1980', '%d/%m/%Y').date()
    users_to_preload = {
        models.User(username="test_admin", email="asdf@asdf.com", password=guard.encrypt_password("9409u8fgrejki0"), name="Someone Person", dob=date, roles="admin"),
        models.User(username="test_coordinator", email="asdf@asdf.com", password=guard.encrypt_password("9409u8fgrejki0"), name="Someone Person the 2nd", dob=date, roles="coordinator"),
        models.User(username="test_rider", email="asdf@asdf.com", password=guard.encrypt_password("9409u8fgrejki0"), name="Someone Person the 2nd", dob=date, roles="rider")
    }

    for user in users_to_preload:
        if is_username_present(user.username):
            print('{} already present in db, skipping'.format(user.username))
        else:
            db.session.add(user)

    db.session.commit()

    yield client

    db.session.remove()
    db.drop_all()
