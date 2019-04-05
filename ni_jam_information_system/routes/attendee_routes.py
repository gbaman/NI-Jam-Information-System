from flask import Blueprint, render_template
import database

from decorators import *

attendee_routes = Blueprint('attendee_routes', __name__,
                        template_folder='templates')


@attendee_routes.route("/workshops")
@attendee_required
@module_booking_required
def display_workshops():
    database.get_schedule_by_time_slot(database.get_current_jam_id(), request.cookies.get('jam_order_id'))
    
    if database.verify_attendee_id(request.cookies.get('jam_order_id'), database.get_current_jam_id()):
        database.get_badges_needed_for_workshop(1)
        workshop_attendees = database.get_attendees_in_order(request.cookies.get("jam_order_id"))
        attendees = []
        if workshop_attendees:
            for attendee in workshop_attendees:
                if attendee.ticket_type == "General Jam Attendee" or attendee.ticket_type == "First-timer":
                    #attendees.append({"name":"{} {} - {}".format(attendee.first_name, attendee.surname, attendee.ticket_type), "id":attendee.attendee_id})
                    attendees.append({"name":"{} {}".format(attendee.first_name, attendee.surname), "id":attendee.attendee_id})
                    return render_template("workshops.html", slots=database.get_schedule_by_time_slot(database.get_current_jam_id(), request.cookies.get('jam_order_id')))
            #return render_template("workshops.html", workshop_slots=database.get_time_slots_to_select(database.get_current_jam_id(), request.cookies.get('jam_order_id')), jam_attendees=attendees)
        #return render_template("workshops.html", workshop_slots=database.get_time_slots_to_select(database.get_current_jam_id(), request.cookies.get('jam_order_id')))
        return render_template("workshops.html", slots=database.get_schedule_by_time_slot(database.get_current_jam_id(), request.cookies.get('jam_order_id')))
    else:
        flash("You must enter your Eventbrite Order ID and the day password to access the workshop booking system.", "danger")
        return redirect("/")




####################################### AJAX Routes #######################################



@attendee_routes.route("/add_workshop_bookings_ajax", methods=['GET', 'POST'])
@attendee_required
@module_booking_required
def add_workshop_bookings_ajax():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.add_attendee_to_workshop(database.get_current_jam_id(), attendee_id, workshop_id):
        return("")


@attendee_routes.route("/remove_workshop_bookings_ajax", methods=['GET', 'POST'])
@attendee_required
@module_booking_required
def remove_workshop_bookings_ajax():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.remove_attendee_to_workshop(database.get_current_jam_id(), attendee_id, workshop_id):
        return("")


@attendee_routes.route("/update_booked_in_count", methods=['GET', 'POST'])
@attendee_required
@module_booking_required
def update_booked_in_count_ajax():
    workshop_id = request.form['workshop_id']
    workshop_run = database.get_workshop_run(workshop_id)
    if workshop_run:
        if int(workshop_run.workshop_room.room_capacity) < int(workshop_run.workshop.workshop_limit):
            max_attendees = workshop_run.workshop_room.room_capacity
        else:
            max_attendees = workshop_run.workshop.workshop_limit
        return "{}/{}".format(len(workshop_run.attendees), max_attendees)