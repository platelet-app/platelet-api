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
    patch = db.Column(db.String(64))

    def __repr__(self):
        return '<Rider {} in patch {} with vehicle {}>'.format(self.name, self.patch, self.assignedVehicle)


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

    def __repr__(self):
        return '<Task ID {} taken at {} with priority {}>'.format(str(self.id), str(self.timestamp), str(self.priority))


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(64))
    model = db.Column(db.String(64))
    dateOfManufacture = db.Column(db.Date)
    dateOfRegistration = db.Column(db.Date)
    registrationNumber = db.Column(db.String(10))

    def __repr__(self):
        return '<Vehicle {} {} with registration {}>'.format(self.manufacturer, self.model, self.registrationNumber)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    passwordHash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)