from app import db, models
from app.views.functions.userfunctions import is_user_present
import datetime

# Add database entries for tests

date = datetime.datetime.strptime('24/01/1980', '%d/%m/%Y').date()

users_to_preload = [
    models.User(username="admin", email="asdf@asdf.com", password="9409u8fgrejki0", name="Someone Person", dob=date, roles="admin"),
    models.User(username="coordinator", email="asdf@asdf.com", password="9409u8fgrejki0", name="Someone Person the 2nd", dob=date, roles="coordinator"),
    models.User(username="rider", email="asdf@asdf.com", password="9409u8fgrejki0", name="Someone Person the 2nd", dob=date, roles="rider")
]

for user in users_to_preload:
    if is_user_present(user.username):
        print('{} already present in db, skipping'.format(user.username))
    else:
        db.session.add(user)

db.session.commit()
