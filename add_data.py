from app import db, models, guard
import datetime
import sys
import json

insert_data = None

if len(sys.argv) > 0:
    with open(sys.argv[1]) as f:
        insert_data = json.loads(f.read())


for user in insert_data['users']:
    existing = None
    try:
        existing = models.User.query.filter_by(username=user['username']).first()
    except:
        pass
    if existing:
        break

    user['name'] = user['firstname'] + " " + user['secondname']
    user['dob'] = datetime.datetime.strptime(user['dob'], '%d/%m/%Y').date()
    user['address'] = models.Address(**user['address'])
    del user['firstname']
    del user['secondname']
    user_model = models.User(**user)

    db.session.add(user_model)
    db.session.commit()

for loc in insert_data['savedlocations']:

    name = loc["name"]
    address = loc["address"].copy()
    try:
        wards = [ward for ward in loc['wards']]
        del loc["wards"]
    except KeyError:
        print("no wards")
        wards = []
    del loc["name"]
    for ward in wards:
        loc['address'] = models.Address(**address, ward=ward)
        location_model = models.Location(**loc, name="{} - {}".format(name, ward))
        db.session.add(location_model)


    loc['address'] = models.Address(**address)

    print(loc)
    location_model = models.Location(**loc, name=name)

    db.session.add(location_model)
    db.session.commit()


for vehicle in insert_data['vehicles']:
    existing = None
    try:
        existing = models.Vehicle.query.filter_by(name=vehicle['name']).first()
    except:
        pass
    if existing:
        break
    vehicle_model = models.Vehicle(**vehicle)

    db.session.add(vehicle_model)
    db.session.commit()

db.session.commit()
