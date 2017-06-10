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

        found_attendee = db_session.query(Attendee).filter(Attendee.attendee_id == attendee["id"]).first()

        try:
            school = attendee["answers"][2]["answer"]
        except KeyError:
            school = None
        if found_attendee:
            new_attendee = found_attendee
        else:
            new_attendee = Attendee()

        new_attendee.attendee_id = attendee["id"],
        new_attendee.first_name = attendee["profile"]["first_name"],
        new_attendee.surname = attendee["profile"]["last_name"],
        new_attendee.age = attendee["profile"].get("age"),
        new_attendee.email_address = "Unknown",
        new_attendee.gender = attendee["profile"]["gender"],
        new_attendee.town = attendee["answers"][0]["answer"],
        new_attendee.experience_level = str(attendee["answers"][1]["answer"]).split()[0],
        new_attendee.school = school,
        new_attendee.order_id = attendee["order_id"],
        new_attendee.ticket_type = attendee["ticket_class_name"]

        if attendee["order_id"] == 788232605:
            print()


        if not found_attendee:
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

def get_time_slots_to_select(jam_id, user_id):
    workshop_slots = []
    for workshop_slot in db_session.query(WorkshopSlot):
        workshop_slots.append({"title":str("{} - {}".format(workshop_slot.slot_time_start, workshop_slot.slot_time_end)), "workshops":[]})
    workshops = db_session.query(RaspberryJamWorkshop, RaspberryJam, WorkshopSlot, Workshop, WorkshopRoom).filter(RaspberryJamWorkshop.jam_id == jam_id,
                                                                                                                           RaspberryJamWorkshop.workshop_room_id == WorkshopRoom.room_id,
                                                                                                                           RaspberryJamWorkshop.slot_id == WorkshopSlot.slot_id,
                                                                                                                           RaspberryJamWorkshop.jam_id == RaspberryJam.jam_id,
                                                                                                                           RaspberryJamWorkshop.workshop_id == Workshop.workshop_id)
    for workshop in workshops:
        if int(workshop.WorkshopRoom.room_capacity) < int(workshop.Workshop.workshop_limit):
            max_attendees = workshop.WorkshopRoom.room_capacity
        else:
            max_attendees = workshop.Workshop.workshop_limit
        names = ""
        for name in get_attendees_in_workshop(workshop.RaspberryJamWorkshop.workshop_run_id):
            if str(name.order_id) == user_id:
                names = "{} {}, ".format(names, name.first_name.capitalize())
        new_workshop = {"workshop_room":workshop.WorkshopRoom.room_name,
                        "workshop_title":workshop.Workshop.workshop_title,
                        "workshop_description":workshop.Workshop.workshop_description,
                        "workshop_limit":"{} / {}".format(len(get_attendees_in_workshop(workshop.RaspberryJamWorkshop.workshop_run_id)), max_attendees),
                        "attendee_names":names,
                        "workshop_id":workshop.RaspberryJamWorkshop.workshop_run_id}

        workshop_slots[workshop.WorkshopSlot.slot_id - 1]["workshops"].append(new_workshop)

    return workshop_slots


def verify_attendee_id(id):
    if id:
        attendees = db_session.query(Attendee).filter(Attendee.order_id == int(id)).all()
        if attendees:
            return attendees
    return False


def get_attendees_in_workshop(workshop_run_id):
    attendees = db_session.query(RaspberryJamWorkshop, WorkshopAttendee, Workshop, Attendee).filter(RaspberryJamWorkshop.workshop_id == Workshop.workshop_id,
                                                                                                    RaspberryJamWorkshop.workshop_run_id == WorkshopAttendee.workshop_run_id,
                                                                                                    Attendee.attendee_id == WorkshopAttendee.attendee_id,
                                                                                                    RaspberryJamWorkshop.workshop_run_id == workshop_run_id).all()
    return_attendees = []
    for a in attendees:
        return_attendees.append(a.Attendee)
    return return_attendees

def get_if_workshop_has_space(jam_id, workshop_run_id):
    workshop = db_session.query(RaspberryJamWorkshop, RaspberryJam, WorkshopSlot, Workshop, WorkshopRoom).filter(
        RaspberryJamWorkshop.jam_id == jam_id,
        RaspberryJamWorkshop.workshop_room_id == WorkshopRoom.room_id,
        RaspberryJamWorkshop.slot_id == WorkshopSlot.slot_id,
        RaspberryJamWorkshop.jam_id == RaspberryJam.jam_id,
        RaspberryJamWorkshop.workshop_id == Workshop.workshop_id,
        RaspberryJamWorkshop.workshop_run_id == workshop_run_id).first()

    if int(workshop.WorkshopRoom.room_capacity) < int(workshop.Workshop.workshop_limit):
        max_attendees = workshop.WorkshopRoom.room_capacity
    else:
        max_attendees = workshop.Workshop.workshop_limit

    if len(get_attendees_in_workshop(workshop_run_id)) < max_attendees:
        return True
    return False

def get_if_attendee_booked_in_slot_for_workshop(attendee_id, workshop_run_id):
    slot_id = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.workshop_run_id == workshop_run_id).first().slot_id

    workshops_attendee_in_slot = db_session.query(RaspberryJamWorkshop, WorkshopAttendee).filter(RaspberryJamWorkshop.workshop_run_id == WorkshopAttendee.workshop_run_id,
                                                                    WorkshopAttendee.attendee_id == attendee_id,
                                                                    RaspberryJamWorkshop.slot_id == slot_id).all()
    if workshops_attendee_in_slot:
        return True
    return False


def add_attendee_to_workshop(jam_id, attendee_id, workshop_run_id):
    attendee = db_session.query(Attendee).filter(Attendee.attendee_id == attendee_id).first()
    if get_if_workshop_has_space(jam_id, workshop_run_id) and not str(attendee.ticket_type).startswith("Parent") and not get_if_attendee_booked_in_slot_for_workshop(attendee_id, workshop_run_id):
        workshop_attendee = WorkshopAttendee(attendee_id=attendee_id, workshop_run_id=workshop_run_id)
        db_session.add(workshop_attendee)
        db_session.commit()
        return True
    else:
        return False
