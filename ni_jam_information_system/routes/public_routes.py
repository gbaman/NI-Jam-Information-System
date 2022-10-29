import random
import time

import pytz as pytz
from flask import Blueprint, render_template, request, make_response, redirect, flash, send_file, abort
import database
from datetime import datetime, timedelta

import emails
from secrets.config import *
import forms as forms
from decorators import *
import configuration
import ics
from dateutil import tz


public_routes = Blueprint('public_routes', __name__,
                        template_folder='templates')


@public_routes.route('/', methods=['POST', 'GET'])
def index():
    if not configuration.verify_config_item_bool("modules", "module_core"):
        return "Core module not enabled. Enable it by adding under the [modules] section in {}, module_core = true.".format(configuration.config_file_location)
    cookie = request.cookies.get('jam_order_id')
    if cookie and len(cookie) == 9 and database.verify_attendee_id(cookie, database.get_current_jam_id()):
        return redirect("workshops")
    form = forms.GetOrderIDForm(request.form)
    if request.method == 'POST' and form.validate():
        day_password = database.get_jam_password()
        if database.verify_attendee_id(form.order_id.data, database.get_current_jam_id()) and day_password and form.day_password.data == day_password:
            resp = make_response(redirect("workshops"))
            resp.set_cookie('jam_order_id', str(form.order_id.data), expires=(datetime.now() + timedelta(hours=6)))
            resp.set_cookie('jam_id', str(database.get_current_jam_id()))
            return resp
        else:
            flash("Error, no order with that ID found or Jam password is wrong. Please try again.", "danger")
            return render_template('index.html', form=form)
    return render_template('index.html', form=form)


@public_routes.route("/qr/<order_id>/<password>") # Allow attendees to be logged into NIJIS via a badge QR code
@module_core_required
def attendee_qr_login(order_id, password):
    day_password = database.get_jam_password()
    if database.verify_attendee_id(order_id, database.get_current_jam_id()) and day_password and password == day_password:
        resp = make_response(redirect("/workshops"))
        resp.set_cookie('jam_order_id', str(order_id), expires=(datetime.now() + timedelta(hours=6)))
        resp.set_cookie('jam_id', str(database.get_current_jam_id()))
        return resp
    else:
        return "Invalid data from QR code..."


@public_routes.route("/login", methods=['POST', 'GET'])
@module_core_required
def login():
    cookie_value = request.cookies.get("jam_login")
    next = logins.get_redirect_target()
    if cookie_value:
        valid, cookie = logins.validate_cookie(cookie_value)
        if valid:
            return redirect('admin/admin_home')

    form = forms.LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        login_validated, user = logins.validate_login(form.username.data, form.password.data)
        if login_validated:
            resp = make_response(logins.redirect_back('admin_routes.admin_home'))
            resp.set_cookie("jam_login", database.new_cookie_for_user(user.user_id))
            return resp
        if user:
            flash("This user account has been disabled and so can not be logged into.", "danger")
        else:
            flash("Unable to login, credentials incorrect.", "danger")
        return render_template("login.html", form=form)
    return render_template("login.html", next=next, form=form)


@public_routes.route("/register", methods=['POST', 'GET'])
@module_core_required
def register():
    form = forms.RegisterUserForm(request.form)
    if request.method == 'POST' and form.validate():
        if form.access_code.data == access_code and not database.get_user_details_from_username(form.username.data):
            salt, bcrypt_password = logins.create_password_salt(form.password.data)
            database.create_user(form.username.data, bcrypt_password, salt, form.first_name.data, form.surname.data, form.email.data, form.dob.data)
            return 'New user account created! <meta http-equiv="refresh" content="3;url=/login" />'
        return "Error, unable to create user account. User may already exist or access code may be incorrect"
    return(render_template("register.html", form=form))


@public_routes.route("/reset_password_with_reset_code", methods=['GET', 'POST'])
@module_core_required
def reset_password_with_reset_code():
    form = forms.ResetPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        user = database.get_user_details_from_username(form.username.data)
        if user.reset_code and str(user.reset_code) == form.reset_code.data:
            logins.update_password(user, form.new_password.data)
            flash("Password reset complete - You can now log in.", "success")
            return redirect("/login")
        flash("Password reset failed, credentials provided were invalid.")
        return render_template("reset_password.html", form=form, error="Reset failed, credentials provided are invalid.")
    return render_template("reset_password.html", form=form)


@public_routes.route("/logout")
@module_core_required
def logout():
    resp = make_response(redirect("/"))
    login_cookie = request.cookies.get("jam_login")
    if login_cookie:
        database.remove_cookie(login_cookie)
    resp.set_cookie('jam_order_id', "", expires=0)
    resp.set_cookie('jam_login', "", expires=0)
    resp.set_cookie('jam_month', "", expires=0)
    return resp


@public_routes.route("/forgotten_password", methods=['GET', 'POST'])
@module_email_required
def forgotten_password():
    form = forms.PasswordResetForm(request.form)
    if request.method == 'POST' and form.validate():
        email_address = form.email_address.data
        maths = form.maths.data
        if maths.lower() == "10" or maths.lower == "ten":
            user = database.get_login_user_from_email(email_address)
            time.sleep(random.uniform(0, 3))
            if user:
                if user.group_id >= 4:
                    flash("This user is trustee or higher level and does not support the forgot my password mechanism. The password for this account must be changed manually.", "danger")
                    return redirect("/login")
                emails.send_password_reset_email(user)
            flash("If user exists, password reset has been sent", "success")
        else:
            flash("Incorrect answer to maths question...", "danger")
    return render_template("forgotten_password.html", form=form)


@public_routes.route("/password_reset_url/<reset_key>", methods=['GET', 'POST'])
@module_email_required
def password_reset_url(reset_key):
    form = forms.ChangePasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        if database.verify_password_reset_url(form.url_key.data):
            user = database.get_user_from_password_reset_url(form.url_key.data)
            logins.update_password(user, form.new_password.data)
            emails.send_password_reset_complete_email(user)
            flash("Password reset complete. You can now log in.", "success")
            return redirect("/login")

    elif database.verify_password_reset_url(reset_key):
        form.url_key.default = reset_key
        form.process()
        return render_template("change_password.html", form=form)
    flash("Invalid password reset URL", "danger")
    return redirect(url_for("public_routes.forgotten_password"))


@public_routes.route("/public_schedule")
@public_routes.route("/public_schedule/<jam_id>")
@module_public_schedule_required
def public_schedule(jam_id=None):
    if not jam_id: 
        jam_id = database.get_current_jam_id()
    jams = database.get_jams_in_db()
    time_slots, workshop_rooms_in_use =database.get_workshop_timetable_data(jam_id)
    return render_template("public_schedule.html", time_slots=time_slots, workshop_rooms_in_use=workshop_rooms_in_use, total_workshop_rooms=len(workshop_rooms_in_use), container_name = " ", selected_jam=database.get_jam_details(jam_id), jams=jams)


@public_routes.route("/static/files/<int:workshop_id>/<filename>")
@module_workshops_required
def files_download(workshop_id, filename):
    file = database.get_file_for_download(workshop_id, "static/files/{}/{}".format(workshop_id, filename))
    login_status, user = logins.check_allowed(request, 3)
    if file.file_permission == "Public" or (file.file_permission == "Jam team only" and login_status):
        return send_file(file.file_path)
    else:
        abort(404)


@public_routes.route("/ics/<ics_uuid>/<jam_id>.ics")
@public_routes.route("/ics/<ics_uuid>.ics")
@module_volunteer_signup_required
def ics_generate(ics_uuid, jam_id=None):
    hours_offset = 0
    user = database.get_user_from_ics_uuid(ics_uuid)
    cal = ics.Calendar()
    if user:
        volunteer_workshops = database.get_volunteer_signup_workshops_for_jam(jam_id, user)
        london_tz = pytz.timezone('Europe/London')
        utc_tz = pytz.timezone("Etc/UCT")
        for workshop in volunteer_workshops:
            event = ics.Event()
            event.begin = utc_tz.localize(datetime.strptime(f"{str(workshop.jam.date.date())} {workshop.slot.slot_time_start}", "%Y-%m-%d %H:%M:%S")).astimezone(london_tz) - timedelta(hours=hours_offset)
            event.end = datetime.strptime(f"{str(workshop.jam.date.date())} {workshop.slot.slot_time_end}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz.gettz('UTC')).astimezone(london_tz) - timedelta(hours=hours_offset)
            event.name = f"Jam - {workshop.workshop.workshop_title}"
            event.description = f"{workshop.workshop.workshop_description}\n\n Current volunteers\n {', '.join(' '.join((o.first_name, o.surname)) for o in workshop.users)}"
            event.location = workshop.workshop_room.room_name
            cal.events.add(event)
        jams = database.get_jams_in_db()
        for jam in jams:
            if not jam_id or (jam_id and jam.jam_id == jam_id):
                event = ics.Event()
                event.begin = jam.date
                event.make_all_day()
                event.name = jam.name
                cal.events.add(event)
        response = make_response(str(cal))
        response.headers["Content-Disposition"] = "attachment; filename=jam.ics"
        response.headers["Content-Type"] = "text/calendar"
        return response
    return abort(404)


@public_routes.route("/s/<shortened_link>")
@module_link_shortener_required
def shortened_link_redirect(shortened_link):
    links = database.get_links(shortened_link, log=True)
    if links:
        return redirect(links[0].link_url)
    else:
        return redirect("/404")

