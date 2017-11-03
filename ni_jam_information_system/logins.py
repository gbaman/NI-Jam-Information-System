from database import *
import flask_bcrypt

def validate_login(username, password):
    print("Attempting to validate login for {}".format(username))
    user = get_user_details_from_username(username)
    if user:
        if flask_bcrypt.check_password_hash(user.password_hash, password + user.password_salt):
            update_cookie_for_user(user.user_id)
            return True
    return False

def check_logged_in(cookie):
    return True

def check_allowed(request):
    login_user = get_logged_in_user_object_from_cookie(request.cookies.get('jam_login'))
    if not login_user:
        selected_user_group_level = 1
    else:
        selected_user_group_level = login_user.group_id
    group_required = get_group_id_required_for_page(request.path)
    print("Current user group level {} - Trying to access {}".format(selected_user_group_level, group_required))
    if selected_user_group_level >= group_required:
        return True, login_user
    return False, login_user


def create_new_user():
    username = input("Username: ")
    password = input("Password: ")
    first_name = input("First Name:")
    surname = input("Surname: ")
    salt = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
    bcrypt_password = flask_bcrypt.generate_password_hash(password+salt)
    create_user(username, bcrypt_password, salt, first_name, surname)
