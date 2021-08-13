from app import app
from app.api.sockets import socketio
import argparse

parser = argparse.ArgumentParser(description='app root')
parser.add_argument('--host', dest='host', type=str)

args = parser.parse_args()

if __name__ == '__main__':
    socketio.socketIO.run(app, host=args.host)
