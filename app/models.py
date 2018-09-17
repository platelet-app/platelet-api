from app import db
from datetime import datetime


class Rider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    address1 = db.Column(db.String(64))
    address2 = db.Column(db.String(64))
    town = db.Column(db.String(64))
    postcode = db.Column(db.String(7))
    dob = db.Column(db.Date)
    status = db.Column(db.String(64))
    assignedVehicle = db.Column(db.Integer)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    pickupAddress1 = db.Column(db.String(64))
    pickupAddress2 = db.Column(db.String(64))
    pickupTown = db.Column(db.String(64))
    pickupPostcode = db.Column(db.String(7))
    destinationAddress1 = db.Column(db.String(64))
    destinationAddress2 = db.Column(db.String(64))
    destinationTown = db.Column(db.String(64))
    destinationPostcode = db.Column(db.String(7))
    patch = db.Column(db.String(64))
    priority = db.Column(db.Integer)
    finalDuration = db.Column(db.Time)
    miles = db.Column(db.Integer)

