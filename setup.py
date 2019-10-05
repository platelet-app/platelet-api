from app import db, models, guard
import datetime
import sys
import sys
import json

insert_data = None

if sys.argv[2]:
    with open(sys.argv[2]) as f:
        insert_data = json.loads(f.read())


for user in insert_data['users']:
    existing = None
    try:
        existing = models.User.query.filter_by(username=user['username']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.commit()

    user['name'] = user['firstname'] + " " + user['secondname']
    user['dob'] = datetime.datetime.strptime(user['dob'], '%d/%m/%Y').date()
    user['address'] = models.Address(**user['address'])
    del user['firstname']
    del user['secondname']
    user_model = models.User(**user)

    db.session.add(user_model)
    db.session.commit()

for loc in insert_data['savedlocations']:
    existing = None
    try:
        existing = models.User.query.filter_by(name=loc['name']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.commit()
    loc['address'] = models.Address(**loc['address'])
    location_model = models.Location(**loc)

    db.session.add(location_model)
    db.session.commit()


date = datetime.datetime.strptime('01/01/1980', '%d/%m/%Y').date()

password = guard.encrypt_password(sys.argv[1])

address = models.Address(line1="123 Fake Street",
                         town="Asgard",
                         county="Oknuj",
                         country="Azeroth",
                         postcode="BS105ND")

user = models.User(username="admin",
                   email="asdf@asdf.com",
                   password=password,
                   address=address,
                   name="Someone Person",
                   dob=date,
                   roles="admin,coordinator,rider",
                   is_active=True,
                   patch="North")

db.session.add(user)
db.session.commit()
