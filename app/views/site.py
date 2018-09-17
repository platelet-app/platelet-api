
from flask import Blueprint, render_template

from app import db

mod = Blueprint('site', __name__, url_prefix='/site')

@mod.route('new', methods=['GET'])
def startSession():

    return "startsession"

@mod.route("registercord")
def registerCoordinator():
    return "registercoord"


@mod.route("registerrider")
def registerRider():
    return "registerrider"

@mod.route("additem")
def addItem():
    return "additem"



#        <li><a href="{{url_for('addItem')}}">Others</a></li>
