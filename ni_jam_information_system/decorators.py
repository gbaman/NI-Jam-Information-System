from functools import wraps
from flask import request, redirect, url_for, flash

import logins
import configuration


def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        login_status, user = logins.check_allowed(request, 4) # Check if user (via cookie) is allowed to access the page
        request.logged_in_user = user
        if login_status: # If allowed to access the page
            return f(*args, **kwargs)

        if user: # If logged in, but not allowed to access the page
            return redirect("505")

        flash("You do not currently have permission to access the requested page. Please log in first.", "danger")
        return redirect(url_for('public_routes.login', next=request.url)) # If not logged in

    return decorated_function


def volunteer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        login_status, user = logins.check_allowed(request, 3)
        request.logged_in_user = user
        if login_status:
            return f(*args, **kwargs)
        if user:
            return redirect("505")
        flash("You do not currently have permission to access the requested page. Please log in first.", "danger")
        return redirect(url_for('public_routes.login', next=request.url))

    return decorated_function


def attendee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        login_status, user = logins.check_allowed(request, 2)
        request.logged_in_user = user
        if login_status:
            return f(*args, **kwargs)
        if user:
            return redirect("505")
        flash("You must log in via your Eventbrite Order ID and the Day Password before you can access that page.", "danger")
        return redirect(url_for('public_routes.index'))

    return decorated_function


# --------------------------------------------- Modules --------------------------------------------- #


def _module_required(f, modules, *args, **kwargs):
    def decorated_function():
        for module_name in modules:
            if not configuration.verify_config_item_bool("modules", module_name):
                flash("Module {} is not enabled and required for this page.".format(module_name), "danger")
                return redirect("404")
        return f(*args, **kwargs)

    return decorated_function()


def module_core_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return _module_required(f, configuration.Modules.module_core, *args, **kwargs)

    return decorated_function


def module_attendees_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return _module_required(f, configuration.Modules.module_attendees, *args, **kwargs)

    return decorated_function


def module_public_schedule_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return _module_required(f, configuration.Modules.module_public_schedule, *args, **kwargs)

    return decorated_function


def module_booking_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return _module_required(f, configuration.Modules.module_booking, *args, **kwargs)

    return decorated_function


def module_workshops_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return _module_required(f, configuration.Modules.module_workshops, *args, **kwargs)

    return decorated_function


def module_volunteer_attendance_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return _module_required(f, configuration.Modules.module_volunteer_attendance, *args, **kwargs)

    return decorated_function


def module_volunteer_signup_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return _module_required(f, configuration.Modules.module_volunteer_signup, *args, **kwargs)

    return decorated_function


def module_api_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return _module_required(f, configuration.Modules.module_api, *args, **kwargs)

    return decorated_function
