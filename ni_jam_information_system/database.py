from ni_jam_information_system.models import *
import datetime


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import ni_jam_information_system.models
    Base.metadata.create_all(bind=engine)


def convert_to_mysql_datetime(datetime_to_convert: datetime.datetime) -> str:
    f = '%Y-%m-%d %H:%M:%S'
    return datetime_to_convert.strftime(f)


def convert_to_python_datetime(datetime_to_convert: str) -> datetime.datetime:
    f = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.strptime(datetime_to_convert, f)


def get_logged_in_group_from_cookie(db_session, cokkie: str) -> LoginUser:
    found_cookie = db_session.query(LoginCookie).filter(LoginCookie.cookie_value == cokkie).first()
    print(found_cookie)
    if found_cookie:
        print("Cookie correct!")
        return db_session.query(LoginUser).filter(LoginUser.login_cookie_id == found_cookie.cookie_id).first()

def get_group_id_required_for_page(page_url):
    page = db_session.query(PagePermission).filter(PagePermission.page_name == page_url).first()
    if page:
        return page.group_required
    else:
        return 0

def add_jam(eventbrite_id, jam_name, date):
    jam = RaspberryJam(jam_id=eventbrite_id, name=jam_name, date=date)

    db_session.add(jam)
    db_session.commit()

def get_jams_in_db():
    return db_session().query(RaspberryJam).all()

def get_jams_dict():
    jams = get_jams_in_db()
    jams_list = []
    for jam in jams:
        jams_list.append({"jam_id": jam.jam_id, "name":jam.name, "date":jam.date})
    return jams_list