from app import ma
from app import models

class UserSchema(ma.Schema):
    class Meta:
        model = models.User
        fields = ('id', 'username', 'name', 'email',
                  'address1', 'address2', 'town',
                  'county', 'country', 'postcode', 'dob', 'patch', 'roles')

    username = ma.Str(required=True)
    email = ma.Email()
    postcode = ma.Function(lambda obj: obj.postcode.upper())
    dob = ma.DateTime(format='%d/%m/%Y')

class UserAddressSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('id', 'name', 'address1', 'address2', 'town',
                  'county', 'country', 'postcode')

    postcode = ma.Function(lambda obj: obj.postcode.upper())

class SessionSchema(ma.ModelSchema):
    class Meta:
        model = models.Session
        fields = ('id', 'user_id', 'timestamp')


class TaskSchema(ma.ModelSchema):
    class Meta:
        model = models.Task
        fields = ('pickupAddressOne', 'pickupAddressTwo', 'pickupAddressTown', 'pickupTown', 'pickupPostcode',
                  'destinationAddressOne', 'destinationAddressTwo', 'destinationTown', 'destinationPostcode',
                  'patch', 'contactName', 'contactNumber', 'priority', 'session', 'timestamp')
