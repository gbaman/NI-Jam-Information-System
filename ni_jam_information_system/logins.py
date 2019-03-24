import datetime
import string
from typing import Optional

import database
import flask_bcrypt
import random
from urllib.parse import urlparse, urljoin
from flask import request, url_for, redirect, flash

import models


def validate_login(username, password):
    print("Attempting to validate login for {}".format(username))
    user = database.get_user_details_from_username(username)
    if user:
        if flask_bcrypt.check_password_hash(user.password_hash, password + user.password_salt):
            if user.active:
                return True, user
            return False, user
    return False, None


def check_allowed(request, group_required):
    valid_cookie, cookie = validate_cookie(request.cookies.get('jam_login'))
    if not valid_cookie:
        if cookie:
            flash("Cookie expired, please log in again.", "danger")
        login_user = None
        selected_user_group_level = 1
        order_id = request.cookies.get('jam_order_id')
        if order_id and database.verify_attendee_id(order_id, database.get_current_jam_id()):
            selected_user_group_level = 2
    else:
        selected_user_group_level = cookie.user.group_id
        login_user = cookie.user
    print("Current user group level {} - Trying to access {} - {}".format(selected_user_group_level, group_required, request.path))
    if selected_user_group_level >= group_required:
        return True, login_user
    return False, login_user


def validate_cookie(cookie_id):
    cookie = database.get_cookie(cookie_id)
    if cookie and cookie.cookie_expiry:
        if cookie.cookie_expiry > datetime.datetime.now():
            database.update_cookie_expiry(cookie.cookie_id)
            return True, cookie
        return False, cookie
    return False, None


def create_password_salt(password):
    salt = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
    bcrypt_password = flask_bcrypt.generate_password_hash(password + salt)
    return salt, bcrypt_password


def create_new_user(group_id=1):
    username = input("Username: ")
    password = input("Password: ")
    first_name = input("First Name:")
    surname = input("Surname: ")
    email = input("Email: ")
    salt, bcrypt_password = create_password_salt(password)
    database.create_user(username, bcrypt_password, salt, first_name, surname, email, group_id)


# Methods from http://flask.pocoo.org/snippets/62/
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


def redirect_back(endpoint, **values):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


def get_current_user() -> Optional[models.LoginUser]:
    if request.cookies.get('jam_login'):
        return database.get_user_from_cookie(request.cookies.get('jam_login'))
    return None 