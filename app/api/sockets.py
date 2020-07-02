from flask import jsonify
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app import app, api_version
import redis
from rq import Queue, Connection
from threading import Lock

thread = None
thread_lock = Lock()

namespace = "/api/{}/subscribe".format(api_version)


@socketio.on('subscribe', namespace=namespace)
def subscribe_to_object(obj_uuid):
    join_room(obj_uuid)
    emit('response', {'data': "Subscribed to object with uuid {}.".format(obj_uuid)})


@socketio.on('unsubscribe', namespace=namespace)
def unsubscribe_from_object(obj_uuid):
    print("yay")
    leave_room(obj_uuid)
    emit('response', {'data': "Unsubscribed from object with uuid {}.".format(obj_uuid)})


@socketio.on('my broadcast event', namespace='/test')
def test_message(message):
    print("yayay")
    emit('my response', {'data': message['data']}, broadcast=True)


@socketio.on('connect', namespace=namespace)
def test_connect():
    print("client connected")
    emit('my response', {'data': 'Connected'})


@socketio.on('disconnect', namespace=namespace)
def test_disconnect():
    print('Client disconnected')


@socketio.on('authenticated', namespace=namespace)
def test_authenticated():
    print('Authed')


def subscribe_to_uuid(subscribed_uuid):
    while True:
        socketio.sleep(2)
        print("aaaaaaaaa")
        socketio.emit('subscription_response',
                      {'data': 'Subscription event', 'payload': "aaa"},
                      namespace=namespace)

        print(get_status(subscribed_uuid))


def get_status(subscribed_uuid):
    with Connection(redis.from_url(app.config["REDIS_URL"])):
        q = Queue()
        jobs = q.jobs
        # task = q.fetch_job(task_id)

    print(jobs)

    results = list(filter(lambda job: job.object_uuid == subscribed_uuid, jobs))
    return results
    if results:
        return results
        response_object = {
            "status": "success",
            "data": {
                "task_id": task.get_id(),
                "task_status": task.get_status(),
                "task_result": task.result,
            },
        }
    else:
        response_object = {"status": "error"}
    return jsonify(response_object)
