from flask import Blueprint, abort

import database
import json
import eventbrite_interactions
from datetime import datetime, time

from models import FileTypeEnum
from secrets.config import *
from decorators import *
import notificiations

api_routes = Blueprint('api_routes', __name__,
                        template_folder='templates')


@api_routes.route("/api/users_not_responded/<token>")
@module_api_required
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
@module_api_required
def get_jam_info(token):
    if token in api_keys:
        jam = eventbrite_interactions.get_eventbrite_event_by_id(database.get_current_jam_id())
        to_return = [jam["name"]["text"], (database.convert_to_python_datetime(jam["start"]["local"].replace("T", " ")) - datetime.now()).days]
        return json.dumps(to_return)
    else:
        return "[]"


@api_routes.route("/api/current_jam_info_post", methods=['POST'])
@module_api_required
@api_key_required
def get_jam_info_post():
        jam = eventbrite_interactions.get_eventbrite_event_by_id(database.get_current_jam_id())
        to_return = {
            "name": jam["name"]["text"],
            "jam_id": database.get_current_jam_id()
        }
        return json.dumps(to_return)


@api_routes.route("/api/equipment/<token>")
@module_api_required
def get_equipment(token):
    if token in api_keys:
        equipment = database.get_all_equipment()
        data = ([dict(equipment_id=e.equipment_id, equipment_name=e.equipment_name, equipment_code=e.equipment_code, equipment_entries=[dict(equipment_entry_id=ee.equipment_entry_id, equipment_entry_number=str(ee.equipment_entry_number).zfill(3)) for ee in e.equipment_entries]) for e in equipment])
        data = json.dumps(data)
        return data
    abort(401, "API key incorrect")


@api_routes.route("/api/equipment_groups/<token>")
@module_api_required
def get_equipment_groups(token):
    if token in api_keys:
        equipment_groups = database.get_equipment_groups()
        data = [dict(equipment_group_id=e.equipment_group_id, equipment_group_name=e.equipment_group_name) for e in equipment_groups]
        return json.dumps(data)
    abort(401, "API key incorrect")


@api_routes.route("/api/add_equipment_entries/<token>", methods=['POST'])
@module_api_required
def add_equipment_entries(token):
    if token in api_keys:
        equipment_id = int(request.form['equipment_id'])
        quantity = int(request.form['quantity'])

        nums_created = database.add_equipment_entries(equipment_id, quantity)
        return json.dumps(nums_created)
    abort(401, "API key incorrect")


@api_routes.route("/api/add_equipment/", methods=['POST'])
@module_api_required
@api_key_required
def add_equipment():
    equipment_name = request.form['equipment_name']
    equipment_code = request.form['equipment_code']
    equipment_group_id = request.form['equipment_group_id']
    if len(equipment_code) != 3:
        abort(400)
    if database.add_equipment(equipment_name, str(equipment_code).upper(), equipment_group_id):
        return ""
    abort(400)


@api_routes.route("/api/upload_pinet_usernames", methods=['POST'])
@module_api_required
@api_key_required
def upload_pinet_usernames():
    raw_data = request.get_json()
    if raw_data:
        data = json.loads(raw_data)
        database.add_pinet_usernames(data["usernames"])
        return "Success"
    return "Failed to import usernames"


@api_routes.route("/api/general_stats", methods=['POST'])
@module_api_required
@api_key_required
def general_api_stats():
    data_to_return = {
        "total_workshop_bookings": database.get_all_workshop_bookings_count(),
        "total_jams": len(database.get_jams_in_db()),
        "total_attendees": database.get_all_attendees_count(),
    }
    return json.dumps(data_to_return)


@api_routes.route("/api/get_jam_day_password", methods=['POST'])
@module_api_required
@api_key_required
def get_jam_day_password():
    jam_id = None
    raw_data = request.get_json()
    if raw_data:
        data = json.loads(raw_data)
        if "jam_id" in data:
            jam_id = int(data["jam_id"])
    database.get_jam_password(jam_id)

    data_to_return = {
        "jam_day_password": database.get_jam_password(jam_id),
    }
    return json.dumps(data_to_return)


@api_routes.route("/api/trigger_notifications", methods=['GET'])
@module_api_required
@module_notification_required
@api_key_required
def trigger_notifications(): # Currently just sends a Jam summery
    volunteers = database.get_attending_volunteers(jam_id=database.get_current_jam_id())[0]
    for volunteer in volunteers:
        notificiations.send_jam_sessions_summery(volunteer)
    return "Sent"


@api_routes.route("/api/trigger_notifications_latecomers", methods=['GET'])
@module_api_required
@module_notification_required
@api_key_required
def trigger_notifications_latecomers(): 
    return notificiations.send_latecomer_workshop_signup_reminder()


@api_routes.route("/api/eventbrite_webhook/<webhook_key>", methods=['POST'])
def eventbrite_webhook(webhook_key):
    db_webhook_key = database.get_eventbrite_webhook_key()
    if webhook_key:
        if db_webhook_key == webhook_key:
            data = request.json
            if "api_url" in data:
                if "orders" in data["api_url"] or "attendee" in data["api_url"]:
                    current_jam = database.get_current_jam_id()
                    if data["config"] and data["config"]["action"] and data["config"]["action"] == "barcode.checked_in":
                        database.update_single_attendee_check_in_from_eventbrite(current_jam, int(data["api_url"].split("attendees/")[1].split("/")[0]), True)
                    return ""
    abort(405)

@api_routes.route("/api/get_schedule/<jam_id>", methods=['GET'])
@api_routes.route("/api/get_schedule", methods=['GET'])
@module_api_required
@module_public_schedule_required
@api_key_required
def get_schedule(jam_id=None):
    def custom_json_converter(o):
        if isinstance(o, time):
            return o.__str__()

    if not jam_id:
        jam_id = database.get_current_jam_id()
    time_slots, workshop_rooms_in_use = database.get_workshop_timetable_data(jam_id, include_hidden_time_slots=True)
    data_to_return = {"time_slots":{}}
    for slot in time_slots:

        workshops_runs = {}
        for workshop in slot.workshops_in_slot:
            if workshop.jam_id == jam_id:
                workshop_files = {}
                for workshop_file in workshop.workshop.workshop_files:
                    workshop_files[workshop_file.file_id] = {"file_path":workshop_file.file_path,
                                                             "file_title": workshop_file.file_title,
                                                             "file_type": workshop_file.file_type.name,
                                                             "file_permission": workshop_file.file_permission}
                workshops_runs[workshop.workshop_run_id] = {"pair": workshop.pair,
                                                            "pilot":workshop.pilot,
                                                            "workshop_id":workshop.workshop.workshop_id,
                                                            "workshop_title":workshop.workshop.workshop_title,
                                                            "workshop_description":workshop.workshop.workshop_description,
                                                            "workshop_hidden": workshop.workshop.workshop_hidden,
                                                            "workshop_url": workshop.workshop.workshop_url,
                                                            "workshop_files": workshop_files,
                                                            }
        data_to_return["time_slots"][slot.slot_id] = {"slot_time_start":slot.slot_time_start,
                                                      "slot_time_end":slot.slot_time_end,
                                                      "slot_hidden":slot.slot_hidden,
                                                      "workshops_run": workshops_runs}

    return json.dumps(data_to_return, default=custom_json_converter)

