import uuid
from flask import Flask, render_template, request, g
from flask_mail import Mail
from flask_reuploads import UploadSet, configure_uploads, ALL
from secrets.config import db_user, db_pass, db_name, db_host

import logins
import database as database
import configuration
from secrets import config
import models

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://{}:{}@{}/{}?charset=utf8'.format(db_user, db_pass, db_host, db_name)

models.db.init_app(app)
with app.app_context():
    models.db.create_all()

with app.app_context():
    if database.first_time_setup():
        print("Setting up super admin account...")
        logins.create_new_user(group_id=4)
        print("A super admin user is now set up. You can now log in using this account.")
        print("Once logged in, add a Raspberry Jam via the Add Jam page, then set up workshop rooms and slots times.")
        print(10 * "\n")

from routes.api_routes import api_routes
from routes.public_routes import public_routes
from routes.attendee_routes import attendee_routes
from routes.admin_routes import admin_routes
from routes.misc_routes import misc_routes
from routes.trustee_routes import trustee_routes



# Setup files uploading with flask_uploads
SUPPORTED_FILES = tuple("pdf ppt py".split())
files = UploadSet("jamDocs", SUPPORTED_FILES)

app.config["UPLOADS_DEFAULT_DEST"] = "static/files"
app.config["WTF_CSRF_ENABLED"] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

configure_uploads(app, files)

app.secret_key = str(uuid.uuid4()).replace("-", "")[:10]

app.register_blueprint(api_routes)
app.register_blueprint(public_routes)
app.register_blueprint(attendee_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(misc_routes)
app.register_blueprint(trustee_routes, url_prefix="/trustee")

configuration.output_modules_enabled()

if configuration.verify_modules_enabled().module_email: 
    mail_settings = {
        "MAIL_SERVER": 'smtp.gmail.com',
        "MAIL_PORT": 465,
        "MAIL_USE_TLS": False,
        "MAIL_USE_SSL": True,
        "MAIL_USERNAME": config.email_username,
        "MAIL_PASSWORD": config.email_password
    }
    app.config.update(mail_settings)
    mail = Mail(app)

if configuration.verify_modules_enabled().module_finance:
    import google_sheets

#if configuration.verify_modules_enabled().module_badge:
#    database.verify_all_workshop_badges_exist()

@app.teardown_appcontext
def shutdown_session(exception=None):
    database.db_session.remove()


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.context_processor
def inject_config_data():
    return dict(modules_enabled=configuration.verify_modules_enabled(),
                jam_organisation_name=configuration.verify_config_item("general", "jam_organisation_name"),
                short_jam_organisation_name=configuration.verify_config_item("general", "short_jam_organisation_name"),
                base_url=configuration.verify_config_item("general", "base_url"))


@app.before_request
def before_request():
    g.user = database.get_user_from_cookie(request.cookies.get('jam_login'))


@app.context_processor
def inject_user_data():
    return dict(logged_in_user=g.user,
                logged_in_attendees=database.get_attendees_in_order(request.cookies.get('jam_order_id'), current_jam=True, ignore_parent_tickets=False).all())


@app.template_filter("remove_duplicates")
def remove_duplicates(list_one, list_two):
    return list(set(list_one) - set(list_two))


if __name__ == '__main__':
    app.run()
