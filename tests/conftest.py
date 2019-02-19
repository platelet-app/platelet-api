import pytest
from app import db, models
from app.views.functions.userfunctions import is_username_present
import datetime


@pytest.fixture(scope="session")
def preload_db(request):
    date = datetime.datetime.strptime('24/01/1980', '%d/%m/%Y').date()

    users_to_preload = {
        models.User(username="test_admin", email="asdf@asdf.com", password="9409u8fgrejki0", name="Someone Person", dob=date, roles="admin"),
        models.User(username="test_coordinator", email="asdf@asdf.com", password="9409u8fgrejki0", name="Someone Person the 2nd", dob=date, roles="coordinator"),
        models.User(username="test_rider", email="asdf@asdf.com", password="9409u8fgrejki0", name="Someone Person the 2nd", dob=date, roles="rider")
    }

    for user in users_to_preload:
        if is_username_present(user.username):
            print('{} already present in db, skipping'.format(user.username))
        else:
            db.session.add(user)

    db.session.commit()

    def unload_db():
        for user in users_to_preload:
            db.session.delete(user)

        possible_user_list = ("test_user", "second_test_user", "changed_username")  # TODO cleaner
        for username in possible_user_list:
            user = models.User.query.filter_by(username=username).first()
            if user:
                db.session.delete(user)

        db.session.commit()

    request.addfinalizer(unload_db)
