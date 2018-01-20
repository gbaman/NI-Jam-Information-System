from flask import Blueprint, render_template, request, make_response, redirect, flash
import database
from datetime import datetime, timedelta
from secrets.config import *
import forms as forms
import logins


public_routes = Blueprint('public_routes', __name__,
                        template_folder='templates')


@public_routes.route('/', methods=['POST', 'GET'])
def index():
    cookie = request.cookies.get('jam_order_id')
    if cookie and len(cookie) == 9 and database.verify_attendee_id(cookie, database.get_current_jam_id()):
        return redirect("workshops")
    form = forms.GetOrderIDForm(request.form)
    if request.method == 'POST' and form.validate():
        if database.verify_attendee_id(form.order_id.data, database.get_current_jam_id()) and form.day_password.data == day_password:
            resp = make_response(redirect("workshops"))
            resp.set_cookie('jam_order_id', str(form.order_id.data), expires=(datetime.now() + timedelta(hours=6)))
            resp.set_cookie('jam_id', str(database.get_current_jam_id()))
            return resp
        else:
            return render_template('index.html', form=form, status="Error, no order with that ID found or Jam password is wrong. Please try again")
    return render_template('index.html', form=form)


@public_routes.route("/login", methods=['POST', 'GET'])
def login():
    cookie_value = request.cookies.get("jam_login")
    if cookie_value:
        valid, cookie = logins.validate_cookie(cookie_value)
        if valid:
            return redirect('admin/admin_home')

    form = forms.LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        login_validated, user = logins.validate_login(form.username.data, form.password.data)
        if login_validated:
            resp = make_response(redirect('admin/admin_home'))
            resp.set_cookie("jam_login", database.new_cookie_for_user(user.user_id))
            return resp
        flash("Unable to login, credentials incorrect.", "danger")
        return render_template("login.html", form=form)
    return render_template("login.html", form=form)


@public_routes.route("/register", methods=['POST', 'GET'])
def register():
    form = forms.RegisterUserForm(request.form)
    if request.method == 'POST' and form.validate():
        if form.access_code.data == access_code and not database.get_user_details_from_username(form.username.data):
            salt, bcrypt_password = logins.create_password_salt(form.password.data)
            database.create_user(form.username.data, bcrypt_password, salt, form.first_name.data, form.surname.data, form.email.data)
            return 'New user account created! <meta http-equiv="refresh" content="3;url=/login" />'
        return "Error, unable to create user account. User may already exist or access code may be incorrect"
    return(render_template("register.html", form=form))


@public_routes.route("/reset", methods=['GET', 'POST'])
def reset_password():
    form = forms.ResetPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        salt, hash = logins.create_password_salt(form.new_password.data)
        if database.reset_password(form.username.data, form.reset_code.data, salt, hash):
            return redirect("/login")
        return render_template("reset_password.html", form=form, error="Reset failed, credentials provided are invalid.")
    return render_template("reset_password.html", form=form)


@public_routes.route("/logout")
def logout():
    resp = make_response(redirect("/"))
    login_cookie = request.cookies.get("jam_login")
    if login_cookie:
        database.remove_cookie(login_cookie)
    resp.set_cookie('jam_order_id', "", expires=0)
    resp.set_cookie('jam_login', "", expires=0)
    resp.set_cookie('jam_month', "", expires=0)
    return resp


@public_routes.route("/public_schedule")
def public_schedule():
    time_slots, workshop_rooms_in_use =database.get_workshop_timetable_data(database.get_current_jam_id())
    return render_template("public_schedule.html", time_slots = time_slots, workshop_rooms_in_use = workshop_rooms_in_use, container_name = " ", jam_title = database.get_jam_details(database.get_current_jam_id()).name)
