from app import ma
from app import models

class UserSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('id', 'username', 'name', 'email',
                  'address1', 'address2', 'town',
                  'county', 'country', 'postcode', 'dob', 'patch')

class UserAddressSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('id', 'name', 'address1', 'address2', 'town',
                  'county', 'country', 'postcode')

class SessionSchema(ma.ModelSchema):
    class Meta:
        model = models.Session

