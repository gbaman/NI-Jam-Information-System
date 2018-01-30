from flask import Blueprint, render_template, request, make_response, redirect, flash
import database
import forms as forms
import eventbrite_interactions
from ast import literal_eval

from decorators import *

admin_routes = Blueprint('admin_routes', __name__, template_folder='templates')


@admin_routes.route("/admin/import_attendees_from_eventbrite/<jam_id>")
@super_admin_required
@module_core_required
def import_from_eventbrite(jam_id):
    database.update_attendees_from_eventbrite(jam_id)
    return redirect("/admin/add_jam")


@admin_routes.route("/admin/admin_home")
@volunteer_required
@module_core_required
def admin_home():
    return render_template("admin/admin_home.html", eventbrite_event_name = database.get_jam_details(database.get_current_jam_id()).name)


@admin_routes.route("/admin/add_jam")
@super_admin_required
@module_core_required
def add_jam():
    return render_template("admin/add_jam.html", jams=eventbrite_interactions.get_eventbrite_events_name_id(), jams_in_db=database.get_jams_dict(), current_jam_id=database.get_current_jam_id())


@admin_routes.route("/admin/add_jam/<eventbrite_id>")
@super_admin_required
@module_core_required
def add_jam_id(eventbrite_id):
    eventbrite_jam = eventbrite_interactions.get_eventbrite_event_by_id(eventbrite_id)
    database.add_jam(eventbrite_id, eventbrite_jam["name"]["text"], eventbrite_jam["start"]["local"].replace("T", " "))
    return redirect("/admin/add_jam", code=302)


@admin_routes.route("/admin/delete_jam", methods=['POST', 'GET'])
@super_admin_required
@module_core_required
def delete_jam():
    jam_id = request.form["jam_id"]
    if int(jam_id) == database.get_current_jam_id():
        print("Error, unable to remove Jam as is the current selected Jam {}".format(database.get_current_jam_id()))
        return
    print("Jam being deleted {}.".format(jam_id))
    database.remove_jam(jam_id)
    return " "


@admin_routes.route("/admin/select_jam", methods=['POST', 'GET'])
@super_admin_required
@module_core_required
def select_jam():
    jam_id = request.form["jam_id"]
    if int(jam_id) == database.get_current_jam_id():
        print("Error, unable to select Jam as is the current selected Jam - {}".format(database.get_current_jam_id()))
        return
    print("Jam being selected {}.".format(jam_id))
    database.select_jam(int(jam_id))
    return " "


@admin_routes.route('/admin/manage_workshop_catalog/', methods=['GET', 'POST'])
@admin_routes.route('/admin/manage_workshop_catalog/<workshop_id>', methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def add_workshop_to_catalog(workshop_id = None):
    form = forms.CreateWorkshopForm(request.form)
    if workshop_id and request.method == "GET":
        workshop = database.get_workshop_from_workshop_id(workshop_id)
        form.workshop_title.default = workshop.workshop_title
        form.workshop_description.default = workshop.workshop_description
        form.workshop_limit.default = workshop.workshop_limit
        form.workshop_level.default = workshop.workshop_level
        form.workshop_id.default = workshop.workshop_id
        form.process()
    if request.method == 'POST' and form.validate():
        database.add_workshop(form.workshop_id.data, form.workshop_title.data, form.workshop_description.data, form.workshop_limit.data, form.workshop_level.data)
        return redirect(('admin/manage_workshop_catalog'))
    return render_template('admin/manage_workshop_catalog.html', form=form, workshops=database.get_workshops_to_select())


@admin_routes.route('/admin/add_workshop_to_jam', methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def add_workshop_to_jam():
    form = forms.AddWorkshopToJam(request.form)
    if request.method == 'POST':# and form.validate():
        database.add_workshop_to_jam_from_catalog(database.get_current_jam_id(), form.workshop.data, form.volunteer.data, form.slot.data, form.room.data, int(literal_eval(form.pilot.data)))
        return redirect("/admin/add_workshop_to_jam", code=302)
    return render_template('admin/add_workshop_to_jam_form.html', form=form, workshop_slots=database.get_time_slots_to_select(database.get_current_jam_id(), 0, admin_mode=True))


@admin_routes.route('/admin/delete_workshop/<workshop_id>')
@volunteer_required
@module_workshops_required
def delete_workshop(workshop_id):
    database.delete_workshop(workshop_id)
    return redirect(('admin/manage_workshop_catalog'))


@admin_routes.route('/admin/workshops', methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def admin_workshops():
    return render_template('admin/admin_workshops.html')


@admin_routes.route("/admin/manage_users", methods=['GET', 'POST'])
@super_admin_required
@module_core_required
def manage_users():
    users = database.get_users()
    return render_template("admin/manage_users.html", users=users)


@admin_routes.route("/admin/attendee_list")
@volunteer_required
@module_attendees_required
def attendee_list():
    jam_attendees = database.get_all_attendees_for_jam(database.get_current_jam_id())
    return render_template("admin/attendee_list.html", attendees=jam_attendees)


@admin_routes.route("/admin/volunteer")
@volunteer_required
@module_volunteer_signup_required
def volunteer():
    time_slots, workshop_rooms_in_use = database.get_volunteer_data(database.get_current_jam_id(), request.logged_in_user)
    return render_template("admin/volunteer_signup.html", time_slots = time_slots, workshop_rooms_in_use = workshop_rooms_in_use, current_selected = ",".join(str(x.workshop_run_id) for x in request.logged_in_user.workshop_runs) +",")


@admin_routes.route("/admin/volunteer_attendance", methods=['GET', 'POST'])
@volunteer_required
@module_volunteer_signup_required
def volunteer_attendance():
    volunteer_attendances = database.get_attending_volunteers(database.get_current_jam_id())
    form = forms.VolunteerAttendance(request.form)
    if request.method == 'POST' and form.validate():
        database.add_volunteer_attendance(database.get_current_jam_id(), request.logged_in_user.user_id, int(literal_eval(form.attending_jam.data)), int(literal_eval(form.attending_setup.data)), int(literal_eval(form.attending_packdown.data)), int(literal_eval(form.attending_food.data)), form.notes.data)

        return redirect(("/admin/volunteer_attendance"), code=302)
    return render_template("admin/volunteer_attendance.html", form=form, volunteer_attendances=volunteer_attendances, user_id=request.logged_in_user.user_id, eventbrite_event_name = database.get_jam_details(database.get_current_jam_id()).name)


@admin_routes.route("/admin/manage_attendees")
@volunteer_required
@module_attendees_required
def manage_attendees():
    # TODO : Needs a merge of volunteers and attendees into one, so both can be checked in/out.
    # Getting names of users, but not their volunteer attendance that is needed.
    jam_attendees = database.get_all_attendees_for_jam(database.get_current_jam_id())
    volunteer_attendances = database.get_attending_volunteers(database.get_current_jam_id(), only_attending_volunteers=True)
    for volunteer_attendee in volunteer_attendance:
        pass
    for attendee in jam_attendees:
        if attendee.current_location == "Checked in":
            attendee.bg_colour = database.green
        elif attendee.current_location == "Checked out":
            attendee.bg_colour = database.yellow
        elif attendee.current_location == "Not arrived":
            attendee.bg_colour = database.light_grey

    #jam_attendees = sorted(jam_attendees, key=lambda x: x.order_id, reverse=False)
    jam_attendees = sorted(jam_attendees, key=lambda x: x.current_location, reverse=False)
    return render_template("admin/manage_attendees.html", attendees=jam_attendees)


@admin_routes.route("/admin/fire_list")
@volunteer_required
@module_attendees_required
def fire_list():
    jam_attendees = database.get_all_attendees_for_jam(database.get_current_jam_id())
    return render_template("admin/fire_list.html", attendees=jam_attendees)




####################################### AJAX Routes #######################################




@admin_routes.route("/admin/get_password_reset_code_ajax", methods=['GET', 'POST'])
@super_admin_required
@module_core_required
def get_password_reset_code():
    user_id = request.form['user_id']
    reset_code = database.get_user_reset_code(user_id)
    return "The requested password reset code is - {}".format(reset_code)


@admin_routes.route("/admin/upgrade_to_volunteer_permission_ajax", methods=['GET', 'POST'])
@super_admin_required
@module_core_required
def upgrade_user_permission():
    user_id = request.form['user_id']
    database.set_group_for_user(user_id, 3)
    return ""


@admin_routes.route("/admin/modify_workshop_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def modify_workshop_ajax():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.add_attendee_to_workshop(database.get_current_jam_id(), attendee_id, workshop_id):
        return ("")


@admin_routes.route("/admin/delete_workshop_from_jam_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def delete_workshop_from_jam_ajax():
    workshop_id = request.form['workshop_id']
    database.remove_workshop_from_jam(workshop_id)
    return redirect("/admin/add_workshop_to_jam", code=302)


@admin_routes.route("/admin/check_out_attendee_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_attendees_required
def check_out_attendee_ajax():
    attendee_id = request.form['attendee_id']
    database.check_out_attendee(attendee_id)
    return redirect("/admin/manage_attendees", code=302)


@admin_routes.route("/admin/check_in_attendee_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_attendees_required
def check_in_attendee_ajax():
    attendee_id = request.form['attendee_id']
    database.check_in_attendee(attendee_id)
    return " "


@admin_routes.route("/admin/volunteer_update_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_volunteer_signup_required
def update_volunteer():
    new_sessions = request.json
    sessions = []
    for session in new_sessions:
        if len(session) > 0:
            sessions.append(int(session))
    if database.set_user_workshop_runs_from_ids(request.logged_in_user, database.get_current_jam_id(), sessions):
        return "True"


@admin_routes.route("/admin/update_attendee_info_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_core_required
def update_attendee_info():
    current_jam = database.get_current_jam_id()
    database.update_attendees_from_eventbrite(current_jam)
    return " "