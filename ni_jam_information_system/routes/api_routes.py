from flask import Blueprint
import database
import json
import eventbrite_interactions
from datetime import datetime
from secrets.config import *

api_routes = Blueprint('api_routes', __name__,
                        template_folder='templates')


@api_routes.route("/api/users_not_responded/<token>")
def get_users_not_responded_to_attendance(token):
    if token in api_keys:
        users_not_responded = database.get_users_not_responded_to_attendance(database.get_current_jam_id())
        email_addresses = []
        for user in users_not_responded:
            email_addresses.append(user.email)
        return json.dumps(email_addresses)
    else:
        return "[]"


@api_routes.route("/api/jam_info/<token>")
def get_jam_info(token):
    if token in api_keys:
        jam = eventbrite_interactions.get_eventbrite_event_by_id(database.get_current_jam_id())
        to_return = [jam["name"]["text"], (database.convert_to_python_datetime(jam["start"]["local"].replace("T", " ")) - datetime.now()).days]
        return json.dumps(to_return)
    else:
        return "[]"