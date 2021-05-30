from flask_restx import reqparse, Resource
from app import guard
from app import login_ns as ns
from app.api.login.login_utilities.login_functions import get_jwt_expire_data


parser = reqparse.RequestParser()
parser.add_argument('username')
parser.add_argument('password')


@ns.route('')
class Login(Resource):
    def post(self):
        args = parser.parse_args()
        user = guard.authenticate(args['username'], args['password'])
        access_token = guard.encode_jwt_token(user)
        expires = get_jwt_expire_data(access_token)
        result = {
            "refresh_expiry": expires[0],
            "login_expiry": expires[1],
            "access_token": access_token
        }
        return result, 200


@ns.route('/refresh_token')
class Login(Resource):
    def get(self):
        old_token = guard.read_token_from_header()
        new_token = guard.refresh_jwt_token(old_token)
        expires = get_jwt_expire_data(new_token)
        result = {
            "refresh_expiry": expires[0],
            "login_expiry": expires[1],
            "access_token": new_token
        }
        return result, 200
