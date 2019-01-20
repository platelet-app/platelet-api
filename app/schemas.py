from app import ma
from app import models

class UserSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('id', 'username', 'password', 'name', 'email',
                  'address1', 'address2', 'town',
                  'county', 'country', 'postcode', 'dob', 'patch', 'roles')

    username = ma.Str(required=True)
    email = ma.Email()
    postcode = ma.Function(lambda obj: obj.postcode.upper())
    dob = ma.DateTime(format='%d/%m/%Y')

class UserAddressSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('id', 'name', 'address1', 'address2', 'town',
                  'county', 'country', 'postcode')

    postcode = ma.Function(lambda obj: obj.postcode.upper())

class SessionSchema(ma.Schema):
    class Meta:
        model = models.Session
        fields = ('id', 'user_id', 'timestamp')


class TaskSchema(ma.Schema):
    class Meta:
        model = models.Task
        fields = ('pickupAddress1', 'pickupAddress2', 'pickupTown', 'pickupPostcode',
                  'destinationAddress1', 'destinationAddress2', 'destinationTown', 'destinationPostcode',
                  'patch', 'contactName', 'contactNumber', 'priority', 'session', 'timestamp')

    contactNumber = ma.Int()
    pickupPostcode = ma.Function(lambda obj: obj.postcode.upper())
    destinationPostcode = ma.Function(lambda obj: obj.postcode.upper())
