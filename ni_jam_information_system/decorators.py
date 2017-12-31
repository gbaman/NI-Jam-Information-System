from functools import wraps
from flask import request, redirect, url_for, flash

import logins


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
        return redirect(url_for('login', next=request.url)) # If not logged in
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
        return redirect(url_for('login', next=request.url))
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
        flash("You do not currently have permission to access the requested page. Please log in first.", "danger")
        return redirect(url_for('login', next=request.url))
    return decorated_function
