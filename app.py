from app import app
from app.api.sockets import socketio

if __name__ == '__main__':
    socketio.socketIO.run(app)
