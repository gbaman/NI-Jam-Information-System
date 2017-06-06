from ni_jam_information_system.models import *
from ni_jam_information_system.eventbrite_interactions import get_eventbrite_attendees_for_event
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


def add_workshop(workshop_title, workshop_description, workshop_limit, workshop_level):
    workshop = Workshop(workshop_title = workshop_title, workshop_description = workshop_description, workshop_limit = workshop_limit, workshop_level = workshop_level)
    db_session.add(workshop)
    db_session.commit()


def get_workshops_for_jam(jam_id):
    workshops = []
    for workshop in db_session.query(RaspberryJam, RaspberryJamWorkshop, Workshop).filter(RaspberryJam.jam_id == jam_id, RaspberryJamWorkshop.workshop_id == Workshop.workshop_id):
        workshops.append({"workshop_title":workshop.Workshop.workshop_title, "workshop_description":workshop.Workshop.workshop_description, "workshop_level":workshop.Workshop.workshop_level, "workshop_time":workshop.RaspberryJamWorkshop.workshop_time_slot})
    return workshops


def update_attendees_from_eventbrite(event_id):
    attendees = get_eventbrite_attendees_for_event(event_id)
    for attendee in attendees["attendees"]:

        db_session.query(Attendee).filter(Attendee.attendee_id == attendee["id"]).delete()

        try:
            school = attendee["answers"][2]["answer"]
        except KeyError:
            school = None
        new_attendee = Attendee(
            attendee_id = attendee["id"],
            first_name = attendee["profile"]["first_name"],
            surname = attendee["profile"]["last_name"],
            age = attendee["profile"].get("age"),
            email_address = "Unknown",
            gender = attendee["profile"]["gender"],
            town = attendee["answers"][0]["answer"],
            experience_level = str(attendee["answers"][1]["answer"]).split()[0],
            school = school,
            order_id = attendee["order_id"]
        )
        db_session.add(new_attendee)
    db_session.commit()


def get_attendees_in_order(order_id):
    found_attendees = db_session.query(Attendee).filter(Attendee.order_id == order_id)
    if not found_attendees:
        return None
    else:
        return found_attendees


def get_volunteers_to_select():
    volunteers = db_session.query(LoginUser)
    to_return = []
    for volunteer in volunteers:
        to_return.append((volunteer.user_id, "{} {}".format(volunteer.first_name, volunteer.surname)))
    return to_return


def get_workshops_to_select():
    to_return = []
    for workshop in db_session.query(Workshop):
        to_return.append((workshop.workshop_id, workshop.workshop_title))
    return to_return

def get_time_slots_to_select(jam_id):
    workshop_slots = []
    for workshop_slot in db_session.query(RaspberryJamWorkshop, RaspberryJam, WorkshopSlot, Workshop, WorkshopRoom).filter(RaspberryJamWorkshop.jam_id == jam_id):
        print(workshop_slot.WorkshopSlot.slot_id)


