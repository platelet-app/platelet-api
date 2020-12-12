from app import guard


def get_jwt_expire_data(token):
    jwt_data = guard.extract_jwt_token(token)
    return jwt_data['rf_exp'] * 1000 if jwt_data else None, jwt_data['exp'] * 1000 if jwt_data else None
