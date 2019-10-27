from app import root_ns as ns


@ns.route('/ping', endpoint="api_ping")
def ping():
    return "pong", 200
