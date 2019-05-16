from app import db, models, guard
import datetime
import sys

date = datetime.datetime.strptime('01/01/1980', '%d/%m/%Y').date()

password = guard.encrypt_password(sys.argv[1])

address = models.Address(line1="123 Fake Street",
                         town="Asgard",
                         county="Oknuj",
                         country="Azeroth",
                         postcode="B00B569")

user = models.User(username="admin",
                   email="asdf@asdf.com",
                   password=password,
                   address=address,
                   name="Someone Person",
                   dob=date,
                   roles="admin,coordinator,rider",
                   is_active=True)

db.session.add(user)
db.session.commit()
