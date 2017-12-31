from flask import Blueprint, render_template, request, make_response, redirect, flash
import database
import json
import eventbrite_interactions
from datetime import datetime, timedelta
from secrets.config import *
import forms as forms
import logins

from decorators import *

attendee_routes = Blueprint('attendee_routes', __name__,
                        template_folder='templates')


@attendee_routes.route("/workshops")
@attendee_required
def display_workshops():
    if database.verify_attendee_id(request.cookies.get('jam_order_id'), database.get_current_jam_id()):
        workshop_attendees = database.get_attendees_in_order(request.cookies.get("jam_order_id"))
        attendees = []
        if workshop_attendees:
            for attendee in workshop_attendees:
                attendees.append({"name":"{} {} - {}".format(attendee.first_name, attendee.surname, attendee.ticket_type), "id":attendee.attendee_id})
            return render_template("workshops.html", workshop_slots=database.get_time_slots_to_select(database.get_current_jam_id(), request.cookies.get('jam_order_id')), jam_attendees=attendees)
        return render_template("workshops.html", workshop_slots=database.get_time_slots_to_select(database.get_current_jam_id(), request.cookies.get('jam_order_id')))
    else:
        return redirect("/")

@attendee_routes.route("/add_workshop_bookings_ajax", methods=['GET', 'POST'])
@attendee_required
def add_workshop_bookings_ajax():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.add_attendee_to_workshop(database.get_current_jam_id(), attendee_id, workshop_id):
        return("")


@attendee_routes.route("/remove_workshop_bookings_ajax", methods=['GET', 'POST'])
@attendee_required
def remove_workshop_bookings_ajax():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.remove_attendee_to_workshop(database.get_current_jam_id(), attendee_id, workshop_id):
        return("")