from app import db, models
import datetime

date = datetime.datetime.strptime('24/01/1980', '%d/%m/%Y').date()

admin = models.User(username="admin", email="asdf@asdf.com", password="9409u8fgrejki0",
                    name="Someone Person", dob=date, roles="admin")

coordinator = models.User(username="coordinator", email="asdf@asdf.com", password="9409u8fgrejki0",
                    name="Someone Person the 2nd", dob=date, roles="coordinator")

db.session.add(admin)
db.session.add(coordinator)
db.session.commit()