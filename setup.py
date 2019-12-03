from app import db, models, guard
import datetime
import sys
import sys
import json

insert_data = None

if len(sys.argv) > 1:
    with open(sys.argv[2]) as f:
        insert_data = json.loads(f.read())

for patch in insert_data['patches']:
    existing = None
    try:
        existing = models.Patch.query.filter_by(label=patch['label']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.commit()
        db.session.flush()
    patch_model = models.Patch(**patch)

    db.session.add(patch_model)
    db.session.commit()

for user in insert_data['users']:
    existing = None
    try:
        existing = models.User.query.filter_by(username=user['username']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.commit()
        db.session.flush()

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
        db.session.flush()
    loc['address'] = models.Address(**loc['address'])
    location_model = models.Location(**loc)

    db.session.add(location_model)
    db.session.commit()


for priority in insert_data['priorities']:
    existing = None
    try:
        existing = models.Patch.query.filter_by(label=priority['label']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.commit()
        db.session.flush()
    priority_model = models.Priority(**priority)

    db.session.add(priority_model)
    db.session.commit()

for deliverable in insert_data['deliverables']:
    existing = None
    try:
        existing = models.DeliverableType.query.filter_by(name=deliverable['name']).first()
    except:
        pass
    if existing:
        db.session.delete(existing)
        db.session.commit()
        db.session.flush()
    deliverable_type_model = models.DeliverableType(**deliverable)

    db.session.add(deliverable_type_model)
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
                   display_name="The Admin",
                   dob=date,
                   roles="admin,coordinator,rider",
                   is_active=True,
                   patch_id=1)

coorduser = models.User.query.filter_by(username="coordinator").first()
coorduser.password = guard.encrypt_password(sys.argv[1])
db.session.add(coorduser)

db.session.add(user)
db.session.commit()
