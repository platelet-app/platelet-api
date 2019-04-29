from app import ma
from app import models


class UserSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('uuid', 'username', 'password', 'name', 'email',
                  'address1', 'address2', 'town',
                  'county', 'country', 'postcode', 'dob', 'patch', 'roles')

    username = ma.Str(required=True)
    email = ma.Email()
    postcode = ma.Function(lambda obj: obj.postcode.upper())
    dob = ma.DateTime(format='%d/%m/%Y')


class UserUsernameSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('id', 'username')

    username = ma.Str(required=True)


class UserAddressSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('uuid', 'name', 'address1', 'address2', 'town',
                  'county', 'country', 'postcode')

    postcode = ma.Function(lambda obj: obj.postcode.upper())


class SessionSchema(ma.Schema):
    class Meta:
        model = models.Session
        fields = ('uuid', 'user_id', 'timestamp')


class TaskSchema(ma.Schema):
    class Meta:
        model = models.Task
        fields = ('pickupAddress1', 'pickupAddress2', 'pickupTown', 'pickupPostcode',
                  'destinationAddress1', 'destinationAddress2', 'destinationTown', 'destinationPostcode',
                  'patch', 'contactName', 'contactNumber', 'priority', 'session', 'timestamp')

    contactNumber = ma.Int()
    pickupPostcode = ma.Function(lambda obj: obj.postcode.upper())
    destinationPostcode = ma.Function(lambda obj: obj.postcode.upper())


class VehicleSchema(ma.Schema):
    class Meta:
        model = models.Task
        fields = ('manufacturer', 'model', 'dateOfManufacture', 'dateOfRegistration',
                  'registrationNumber')

    dateOfManufacture = ma.DateTime(format='%d/%m/%Y')
    dateOfRegistration = ma.DateTime(format='%d/%m/%Y')
    registrationNumber = ma.Function(lambda obj: obj.registrationNumber.upper())

