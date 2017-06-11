from models import LoginUser
from database import *

def validate_login(username, password):
    return True

def check_logged_in(cookie):
    return True

def check_allowed(db_session, request):
    login_user = get_logged_in_group_from_cookie(db_session, request.cookies.get('jam_login'))
    if not login_user:
        selected_user_group_level = 0
    else:
        selected_user_group_level = login_user.group_id
    group_required = get_group_id_required_for_page(request.path)
    if selected_user_group_level >= group_required:
        return True, login_user
    return False, login_user

