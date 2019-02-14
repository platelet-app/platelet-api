
from flask import Blueprint, render_template

from app import db

mod = Blueprint('site', __name__, url_prefix='/site')

@mod.route('new', methods=['GET'])
def start_session():

    return "startsession"

@mod.route("registercord")
def register_coordinator():
    return "registercoord"


@mod.route("registerrider")
def register_rider():
    return "registerrider"

@mod.route("additem")
def add_item():
    return "additem"



#        <li><a href="{{url_for('addItem')}}">Others</a></li>
