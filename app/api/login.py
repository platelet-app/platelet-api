from flask_restplus import reqparse, Resource
from app import guard
from app import login_ns as ns
import flask_praetorian


parser = reqparse.RequestParser()
parser.add_argument('username')
parser.add_argument('password')


@ns.route('')
class Login(Resource):
    def post(self):
        args = parser.parse_args()
        user = guard.authenticate(args['username'], args['password'])
        ret = {'access_token': guard.encode_jwt_token(user)}
        return ret, 200


@ns.route('/refresh_token')
class Login(Resource):
    @flask_praetorian.auth_required
    def get(self):
        token = guard.refresh_jwt_token(guard.refresh_jwt_token(guard.read_token_from_header()))
        ret = {'access_token': token}
        return ret, 200
