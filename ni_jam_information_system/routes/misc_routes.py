from flask import Blueprint, render_template


misc_routes = Blueprint('misc_routes', __name__, template_folder='templates')


@misc_routes.route("/505")
def permission_denied():
    return render_template("errors/permission.html"), 505