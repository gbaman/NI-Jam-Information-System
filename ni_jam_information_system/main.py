from flask import Flask, render_template, request, make_response, redirect, flash

app = Flask(__name__)
from datetime import datetime, timedelta
from logins import *
import database as database
import forms as forms
import eventbrite_interactions as eventbrite
from ast import literal_eval
import json
from secrets.config import api_keys


current_jam_id = 39796296795
day_password = "snow"
access_code = "secret-code"


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.before_request
def check_permission():
    permission_granted, user = check_allowed(request)
    print(request.url_root)
    if not permission_granted:
        return render_template("errors/permission.html")
    else:
        request.logged_in_user = user

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.route("/test")
def test():
    pass


@app.route("/admin/import_attendees_from_eventbrite/<jam_id>")
def import_from_eventbrite(jam_id):
    print("Importing...")
    update_attendees_from_eventbrite(jam_id)
    return redirect("/admin/add_jam")

@app.route('/', methods=['POST', 'GET'])
def index():
    cookie = request.cookies.get('jam_order_id')
    if cookie and len(cookie) == 9 and database.verify_attendee_id(cookie):
        return redirect("workshops")
    form = forms.GetOrderIDForm(request.form)
    if request.method == 'POST' and form.validate():
        if database.verify_attendee_id(form.order_id.data) and form.day_password.data == day_password:
            resp = make_response(redirect("workshops"))
            resp.set_cookie('jam_order_id', str(form.order_id.data), expires=(datetime.datetime.now() + timedelta(hours=6)))
            resp.set_cookie('jam_id', str(current_jam_id))
            return resp
        else:
            return render_template('index.html', form=form, status="Error, no order with that ID found or Jam password is wrong. Please try again")
    return render_template('index.html', form=form)


@app.route("/admin/admin_home")
def admin_home():
    return render_template("admin/admin_home.html", eventbrite_event_name = eventbrite.get_eventbrite_event_by_id(current_jam_id)["name"]["text"])


@app.route("/admin/add_jam")
def add_jam():
    return render_template("admin/add_jam.html", jams=eventbrite.get_eventbrite_events_name_id(), jams_in_db=database.get_jams_dict(), current_jam_id = current_jam_id)

@app.route("/admin/add_jam/<eventbrite_id>")
def add_jam_id(eventbrite_id):
    eventbrite_jam = eventbrite.get_eventbrite_event_by_id(eventbrite_id)
    database.add_jam(eventbrite_id, eventbrite_jam["name"]["text"], eventbrite_jam["start"]["local"].replace("T", " "))
    return redirect("/admin/add_jam", code=302)


@app.route("/admin/select_jam", methods=['POST', 'GET'])
def select_jam():
    jam_id = request.form["jam_id"]
    print("Jam being selected {}".format( jam_id))
    return " "

@app.route("/admin/delete_jam", methods=['POST', 'GET'])
def delete_jam():
    jam_id = request.form["jam_id"]
    if int(jam_id) == current_jam_id:
        print("Error, unable to remove Jam as is the current selected Jam")
        return
    print("Jam being deleted {}.".format(jam_id))
    database.remove_jam(jam_id)
    return " "


@app.route("/login", methods=['POST', 'GET'])
def login():
    form = forms.LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        if validate_login(form.username.data, form.password.data):
            resp = make_response(redirect(('admin/admin_home')))
            resp.set_cookie("jam_login", get_cookie_for_username(form.username.data))
            return resp
        print("Failed to login!")
    return(render_template("login.html", form=form))


@app.route("/register", methods=['POST', 'GET'])
def register():
    form = forms.RegisterUserForm(request.form)
    if request.method == 'POST' and form.validate():
        if form.access_code.data == access_code and not get_user_details_from_username(form.username.data):
            salt = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
            bcrypt_password = flask_bcrypt.generate_password_hash(form.password.data + salt)
            database.create_user(form.username.data, bcrypt_password, salt, form.first_name.data, form.surname.data)
            return "New user account created!"
        return "Error, unable to create user account. User may already exist or access code may be incorrect"
    return(render_template("register.html", form=form))


#@app.route("/check_login", methods=['POST', 'GET'])
#def check_login():
#    resp = make_response("Added")
#    resp.set_cookie("jam_login", "12345")
#    return resp

@app.route('/admin/manage_workshop_catalog/', methods=['GET', 'POST'])
@app.route('/admin/manage_workshop_catalog/<workshop_id>', methods=['GET', 'POST'])
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
        print("Thanks for adding")
        return redirect(('admin/manage_workshop_catalog'))
    return render_template('admin/manage_workshop_catalog.html', form=form, workshops=database.get_workshops_to_select())


@app.route('/admin/add_workshop_to_jam', methods=['GET', 'POST'])
def add_workshop_to_jam():
    form = forms.AddWorkshopToJam(request.form)
    if request.method == 'POST':# and form.validate():
        add_workshop_to_jam_from_catalog(current_jam_id, form.workshop.data, form.volunteer.data, form.slot.data, form.room.data, int(literal_eval(form.pilot.data)))
        print("{}  {}   {}".format(form.slot.data, form.workshop.data, form.volunteer.data))
        print("Thanks for adding")
        return redirect("/admin/add_workshop_to_jam", code=302)
    return render_template('admin/add_workshop_to_jam_form.html', form=form, workshop_slots=database.get_time_slots_to_select(current_jam_id, 0, admin_mode=True))


@app.route('/admin/delete_workshop/<workshop_id>')
def delete_workshop(workshop_id):
    database.delete_workshop(workshop_id)
    return redirect(('admin/manage_workshop_catalog'))

@app.route('/admin/workshops', methods=['GET', 'POST'])
def admin_workshops():
    return render_template('admin/admin_workshops.html')


@app.route("/admin/modify_users", methods=['GET', 'POST'])
def modify_users():
    database.get_users()
    render_template()
    # This section is for modifying users, needs wired up with SQL

@app.route("/admin/attendee_list")
def attendee_list():
    jam_attendees = database.get_all_attendees_for_jam(current_jam_id)
    return render_template("admin/attendee_list.html", attendees=jam_attendees)


@app.route("/workshops")
def display_workshops():
    if database.verify_attendee_id(request.cookies.get('jam_order_id')):
        workshop_attendees = get_attendees_in_order(request.cookies.get("jam_order_id"))
        attendees = []
        if workshop_attendees:
            for attendee in workshop_attendees:
                attendees.append({"name":"{} {} - {}".format(attendee.first_name, attendee.surname, attendee.ticket_type), "id":attendee.attendee_id})
            return render_template("workshops.html", workshop_slots=database.get_time_slots_to_select(current_jam_id, request.cookies.get('jam_order_id')), jam_attendees=attendees)
        return render_template("workshops.html", workshop_slots=database.get_time_slots_to_select(current_jam_id, request.cookies.get('jam_order_id')))
    else:
        return redirect("/")


@app.route("/clear_tokens")
def clear_tokens():
    resp = make_response(redirect("/"))
    resp.set_cookie('jam_order_id', "", expires=0)
    resp.set_cookie('jam_login', "", expires=0)
    resp.set_cookie('jam_month', "", expires=0)
    return resp

@app.route("/show_tokens")
def show_tokens():
    order_id = request.cookies.get('jam_order_id')
    jam_login = request.cookies.get('jam_login')
    return("<p> Order ID - {} </p>"
           "<p> Jam Login ID - {} </p>".format(order_id, jam_login))

#@app.route("/clear_db")
#def clear_db():
#    database_reset()
#    return("Reset complete")

@app.route("/add_workshop_bookings_ajax", methods=['GET', 'POST'])
def add_workshop_bookings_ajax():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.add_attendee_to_workshop(current_jam_id, attendee_id, workshop_id):
        return("")


@app.route("/remove_workshop_bookings_ajax", methods=['GET', 'POST'])
def remove_workshop_bookings_ajax():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.remove_attendee_to_workshop(current_jam_id, attendee_id, workshop_id):
        return("")


@app.route("/admin_modify_workshop_ajax", methods=['GET', 'POST'])
def background_test():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    if database.add_attendee_to_workshop(current_jam_id, attendee_id, workshop_id):
        return ("")

@app.route("/delete_workshop_from_jam_ajax", methods=['GET', 'POST'])
def delete_workshop_from_jam_ajax():
    workshop_id = request.form['workshop_id']
    database.remove_workshop_from_jam(workshop_id)
    return redirect("/admin/add_workshop_to_jam", code=302)

@app.route("/admin/volunteer")
def volunteer():
    time_slots, workshop_rooms_in_use = database.get_volunteer_data(current_jam_id, request.logged_in_user)
    return render_template("admin/volunteer_signup.html", time_slots = time_slots, workshop_rooms_in_use = workshop_rooms_in_use, current_selected = ",".join(str(x.workshop_run_id) for x in request.logged_in_user.workshop_runs) +",")

    # TODO : Finish off adding the custom rooms/"workshops" for front desk, parking etc

@app.route("/admin/volunteer_update_ajax", methods=['GET', 'POST'])
def update_volunteer():
    new_sessions = request.json
    sessions = []
    for session in new_sessions:
        if len(session) > 0:
            sessions.append(int(session))
    if database.set_user_workshop_runs_from_ids(request.logged_in_user, current_jam_id, sessions):
        return "True"


@app.route("/admin/volunteer_attendance", methods=['GET', 'POST'])
def volunteer_attendance():
    volunteer_attendances = database.get_attending_volunteers(current_jam_id, request.logged_in_user.user_id)
    form = forms.VolunteerAttendance(request.form)
    if request.method == 'POST' and form.validate():
        add_volunteer_attendance(current_jam_id, request.logged_in_user.user_id, int(literal_eval(form.attending_jam.data)), int(literal_eval(form.attending_setup.data)), int(literal_eval(form.attending_packdown.data)), int(literal_eval(form.attending_food.data)), form.notes.data)

        return redirect(("/admin/volunteer_attendance"), code=302)
    return render_template("admin/volunteer_attendance.html", form=form, volunteer_attendances=volunteer_attendances, user_id=request.logged_in_user.user_id)


@app.route("/api/users_not_responded/<token>")
def get_users_not_responded_to_attendance(token):
    if token in api_keys:
        users_not_responded = database.get_users_not_responded_to_attendance(current_jam_id)
        email_addresses = []
        for user in users_not_responded:
            email_addresses.append(user.email)
        return json.dumps(email_addresses)
    else:
        return "[]"

@app.route("/api/jam_info/<token>")
def get_jam_info(token):
    if token in api_keys:
        jam = eventbrite.get_eventbrite_event_by_id(current_jam_id)
        to_return = [jam["name"]["text"], (datetime.datetime.now() - database.convert_to_python_datetime(jam["start"]["local"].replace("T", " "))).days]
        return json.dumps(to_return)
    else:
        return "[]"


if __name__ == '__main__':
    app.run()