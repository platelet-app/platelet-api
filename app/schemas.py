from app import ma
from app import models

class UserSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('id', 'username', 'name', 'email',
                  'address1', 'address2', 'town',
                  'county', 'country', 'postcode', 'dob', 'patch', 'roles')

class UserAddressSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('id', 'name', 'address1', 'address2', 'town',
                  'county', 'country', 'postcode')

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
