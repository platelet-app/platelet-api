from flask_restful import reqparse, Resource
from app import guard
from app import loginApi as api


parser = reqparse.RequestParser()
parser.add_argument('username')
parser.add_argument('password')

class Login(Resource):

    def post(self):

        args = parser.parse_args()

        user = guard.authenticate(args['username'], args['password'])
        ret = {'access_token': guard.encode_jwt_token(user)}
        return ret, 200

api.add_resource(Login, '')
