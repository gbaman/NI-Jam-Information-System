from flask import Flask, render_template, request, make_response, redirect

app = Flask(__name__)
app.debug = True
#app.run(host='0.0.0.0')
from ni_jam_information_system.eventbrite_interactions import *
from ni_jam_information_system.logins import *
import ni_jam_information_system.database as database

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.before_request
def check_permission():
    permission_granted, user = check_allowed(db_session, request)
    print(request.url_root)
    if not permission_granted:
        return("Not allowed")
    else:
        request.logged_in_user = user


@app.route('/')
def index():
    print("Rendering index")
    return render_template("index.html")

@app.route("/eventbrite")
def eventbrite_check():
    print(request.logged_in_user.password_hash)
    eventbrite_test()
    return("Hello")

@app.route("/admin/add_jam")
def add_jam():
    return render_template("admin/add_jam.html", jams=get_eventbrite_events_name_id(), jams_in_db=database.get_jams_dict())

@app.route("/admin/add_jam/<eventbrite_id>")
def add_jam_id(eventbrite_id):
    eventbrite_jam = get_eventbrite_event_by_id(eventbrite_id)
    database.add_jam(eventbrite_id, eventbrite_jam["name"]["text"], eventbrite_jam["start"]["local"].replace("T", " "))
    return redirect("/admin/add_jam", code=302)

@app.route("/login")
def login():
    return(render_template("login.html"))

@app.route("/check_login", methods=['POST', 'GET'])
def check_login():
    resp = make_response("Added")
    resp.set_cookie("jam_login", "12345")
    return resp