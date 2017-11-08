from flask import Flask, render_template, request, make_response, redirect

app = Flask(__name__)
#app.run(host='0.0.0.0', port=80)
from datetime import datetime, timedelta
from logins import *
import database as database
import forms as forms
import eventbrite_interactions as eventbrite


current_jam_id = 38896532576
day_password = "hello"
access_code = "secret-code"



@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.before_request
def check_permission():
    permission_granted, user = check_allowed(request)
    print(request.url_root)
    if not permission_granted:
        return("You don't have permission to access this page.")
    else:
        request.logged_in_user = user

@app.route("/test")
def test():
    create_new_user()


@app.route("/admin/import_attendees_from_eventbrite")
def import_from_eventbrite():
    print("Importing...")
    update_attendees_from_eventbrite(current_jam_id)
    return("Import finished.")

@app.route('/', methods=['POST', 'GET'])
def index():
    cookie = request.cookies.get('jam_order_id')
    if cookie and len(cookie) == 9 and database.verify_attendee_id(cookie):
        return redirect("workshops")
    form = forms.get_order_ID_form(request.form)
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
    print("Admin home")
    return render_template("admin/admin_home.html")


@app.route("/admin/add_jam")
def add_jam():
    return render_template("admin/add_jam.html", jams=eventbrite.get_eventbrite_events_name_id(), jams_in_db=database.get_jams_dict())

@app.route("/admin/add_jam/<eventbrite_id>")
def add_jam_id(eventbrite_id):
    eventbrite_jam = eventbrite.get_eventbrite_event_by_id(eventbrite_id)
    database.add_jam(eventbrite_id, eventbrite_jam["name"]["text"], eventbrite_jam["start"]["local"].replace("T", " "))
    return redirect("/admin/add_jam", code=302)

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

@app.route('/admin/add_workshop_to_catalog', methods=['GET', 'POST'])
def add_workshop_to_catalog():
    form = forms.CreateWorkshopForm(request.form)
    if request.method == 'POST' and form.validate():
        database.add_workshop(form.workshop_title.data, form.workshop_description.data, form.workshop_limit.data, form.workshop_level.data)
        print("Thanks for adding")
        return redirect(('admin/add_workshop_to_catalog'))
    return render_template('admin/new_workshop_form.html', form=form)


@app.route('/admin/add_workshop_to_jam', methods=['GET', 'POST'])
def add_workshop_to_jam():
    form = forms.add_workshop_to_jam(request.form)
    if request.method == 'POST':# and form.validate():
        add_workshop_to_jam_from_catalog(current_jam_id, form.workshop.data, form.volunteer.data, form.slot.data, form.room.data)
        print("{}  {}   {}".format(form.slot.data, form.workshop.data, form.volunteer.data))
        print("Thanks for adding")
        return redirect("/admin/add_workshop_to_jam", code=302)
    return render_template('admin/add_workshop_to_jam_form.html', form=form, workshop_slots=database.get_time_slots_to_select(current_jam_id, 0, admin_mode=True))


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





if __name__ == '__main__':
    app.run()