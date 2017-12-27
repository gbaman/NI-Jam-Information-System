import string
import database
import flask_bcrypt
import random

def validate_login(username, password):
    print("Attempting to validate login for {}".format(username))
    user = database.get_user_details_from_username(username)
    if user:
        # TODO : Getting invalid salt errors for Sam account...
        if flask_bcrypt.check_password_hash(user.password_hash, password + user.password_salt):
            database.update_cookie_for_user(user.user_id)
            return True
    return False


def check_allowed(request):
    login_user = database.get_logged_in_user_object_from_cookie(request.cookies.get('jam_login'))
    if not login_user:
        selected_user_group_level = 1
        order_id = request.cookies.get('jam_order_id')
        if order_id and database.verify_attendee_id(order_id):
            selected_user_group_level = 2
    else:
        selected_user_group_level = login_user.group_id
    group_required = database.get_group_id_required_for_page(request.path)
    print("Current user group level {} - Trying to access {} - {}".format(selected_user_group_level, group_required, request.path))
    if selected_user_group_level >= group_required:
        return True, login_user
    return False, login_user


def create_password_salt(password):
    salt = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
    bcrypt_password = flask_bcrypt.generate_password_hash(password + salt)
    return salt, bcrypt_password


def create_new_user():
    username = input("Username: ")
    password = input("Password: ")
    first_name = input("First Name:")
    surname = input("Surname: ")
    salt, bcrypt_password = create_password_salt(password)
    database.create_user(username, bcrypt_password, salt, first_name, surname)
