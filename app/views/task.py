from flask import Blueprint, render_template

from app import db

mod = Blueprint('task', __name__, url_prefix='/api/v1/task')

@mod.route('<int:id>', methods=['GET'])
def getTask(id):

    return str(id)


@mod.route('<int:id>/date/recorded', methods=['GET'])
def getTaskDateTime(id):

    return "Date/time {} was recorded".format(str(id))


@mod.route('<int:id>/date/retrieved', methods=['GET'])
def getTaskDateTimeRetrieved(id):

    return "Date/time {} was retrieved".format(str(id))


@mod.route('<int:id>/date/delivered', methods=['GET'])
def getTaskDateTimeDelivered(id):

    return "Date/time {} was delivered".format(str(id))


@mod.route('<int:id>/duration', methods=['GET'])
def getDuration(id):

    return "Delivery duration of {} ".format(str(id))


@mod.route('<int:id>/destination', methods=['GET'])
def getDestination(id):

    return "Delivery duration of {} ".format(str(id))

@mod.route('<int:id>/patch', methods=['GET'])
def getPatch(id):

    return "Delivery patch of {} ".format(str(id))


@mod.route('<int:id>/distance', methods=['GET'])
def getDistance(id):

    return "Can google maps be used for this? {} ".format(str(id))


@mod.route('submit', methods=['PUT'])
def saveTask():
    return "saved... lol not really"


@mod.route('<int:id>/edit', methods=['POST', 'GET'])
def editTask(id):
    return "You tried to edit the task with id {}".format(str(id))