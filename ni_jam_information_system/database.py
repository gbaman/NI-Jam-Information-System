import random
import string
import uuid

from models import *
from eventbrite_interactions import get_eventbrite_attendees_for_event
import datetime
from copy import deepcopy

red = "#fc9f9f"
orange = "#fcbd00"
yellow = "#fff60a"
green = "#c4fc9f"
grey = "#969696"
blue = "#00bbff"


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    Base.metadata.create_all(bind=engine)


def convert_to_mysql_datetime(datetime_to_convert: datetime.datetime) -> str:
    f = '%Y-%m-%d %H:%M:%S'
    return datetime_to_convert.strftime(f)


def convert_to_python_datetime(datetime_to_convert: str) -> datetime.datetime:
    f = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.strptime(datetime_to_convert, f)


def get_logged_in_user_object_from_cookie(cookie: str) -> LoginUser:
    found_cookie = db_session.query(LoginCookie).filter(LoginCookie.cookie_value == cookie).first()
    if found_cookie:
        cookie = db_session.query(LoginUser).filter(LoginUser.login_cookie_id == found_cookie.cookie_id).first()
        #print("Cookie correct! - {}".format(cookie.cookie_id) )
        return cookie

def get_group_id_required_for_page(page_url):
    if page_url.startswith("/static") or page_url.startswith("/template") or page_url.startswith("/api"):
        return 1
    page = db_session.query(PagePermission).filter(PagePermission.page_name == page_url).first()
    if page: # If exact path match
        return page.group_required
    else:
        multi_paths = db_session.query(PagePermission).filter(PagePermission.page_name.contains("*")).all()
        for path in multi_paths: # Iterate across paths with a *
            if page_url.startswith(path.page_name[:-1]):
                return path.group_required
        return 4 # No path found


def add_jam(eventbrite_id, jam_name, date):


    jam = RaspberryJam(jam_id=eventbrite_id, name=jam_name, date=date)

    db_session.add(jam)
    db_session.commit()
    car_parking_workshop = db_session.query(Workshop).filter(Workshop.workshop_title == "Car Parking").first()
    car_parking_room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_name == "Car Park").first()
    car_parking = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=car_parking_workshop.workshop_id, workshop_room_id=car_parking_room.room_id, slot_id=0, pilot=0)
    db_session.add(car_parking)

    front_desk_workshop = db_session.query(Workshop).filter(Workshop.workshop_title == "Front desk").first()
    front_desk_registration_room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_name == "Front Desk Registration").first()
    front_desk_room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_name == "Front Desk General").first()

    front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_registration_room.room_id, slot_id=0, pilot=0)
    db_session.add(front_desk)

    front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_room.room_id, slot_id=1, pilot=0)
    db_session.add(front_desk)
    front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_room.room_id, slot_id=2, pilot=0)
    db_session.add(front_desk)
    front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_room.room_id, slot_id=3, pilot=0)
    db_session.add(front_desk)
    front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_room.room_id, slot_id=4, pilot=0)
    db_session.add(front_desk)

    db_session.commit()

def get_jams_in_db():
    return db_session().query(RaspberryJam).all()

def get_jams_dict():
    jams = get_jams_in_db()
    jams_list = []
    for jam in jams:
        jams_list.append({"jam_id": jam.jam_id, "name":jam.name, "date":jam.date})
    return jams_list


def add_workshop(workshop_id, workshop_title, workshop_description, workshop_limit, workshop_level):

    if workshop_id or workshop_id == 0: # If workshop already exists
        workshop = db_session.query(Workshop).filter(Workshop.workshop_id == workshop_id).first()
        workshop.workshop_title = workshop_title
        workshop.workshop_description = workshop_description
        workshop.workshop_limit = workshop_limit
        workshop.workshop_level = workshop_level
    else: # If new workshop
        workshop = Workshop(workshop_title = workshop_title, workshop_description = workshop_description, workshop_limit = workshop_limit, workshop_level = workshop_level, workshop_hidden = 0)
        db_session.add(workshop)
    db_session.commit()


def get_workshops_for_jam_old(jam_id):
    workshops = []
    for workshop in db_session.query(RaspberryJam, RaspberryJamWorkshop, Workshop).filter(RaspberryJam.jam_id == jam_id, RaspberryJamWorkshop.workshop_id == Workshop.workshop_id):
        workshops.append({"workshop_title":workshop.Workshop.workshop_title, "workshop_description":workshop.Workshop.workshop_description, "workshop_level":workshop.Workshop.workshop_level, "workshop_time":workshop.RaspberryJamWorkshop.workshop_time_slot})
    return workshops


def update_attendees_from_eventbrite(event_id):
    attendees = get_eventbrite_attendees_for_event(event_id)
    for attendee in attendees["attendees"]:

        found_attendee = db_session.query(Attendee).filter(Attendee.attendee_id == attendee["id"]).first()

        if attendee["refunded"] == True:
            if found_attendee:
                db_session.delete(found_attendee)
            continue

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
        new_attendee.jam_id = int(event_id)

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
    return db_session.query(Workshop)


def get_workshop_from_workshop_id(workshop_id):
    return db_session.query(Workshop).filter(Workshop.workshop_id == workshop_id).first()


def get_individual_time_slots_to_select():
    to_return = []
    for time_slots in db_session.query(WorkshopSlot):
        to_return.append((time_slots.slot_id, str(time_slots.slot_time_start)))
    return to_return


def get_workshop_rooms():
    to_return = []
    for workshop_room in db_session.query(WorkshopRoom):
        to_return.append((workshop_room.room_id, workshop_room.room_name))
    return to_return


def get_time_slots_to_select(jam_id, user_id, admin_mode=False):
    workshop_slots = []
    for workshop_slot in db_session.query(WorkshopSlot).filter():
        workshop_slots.append({"title":str("{} - {}".format(workshop_slot.slot_time_start, workshop_slot.slot_time_end)), "workshops":[]})

    workshops = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.jam_id == jam_id)
    if not admin_mode:
        workshops = workshops.filter(RaspberryJamWorkshop.workshop_id == Workshop.workshop_id, Workshop.workshop_hidden != 1)

    for workshop in workshops.all():
        if workshop.workshop.workshop_hidden == 0:
            pass

        if int(workshop.workshop_room.room_capacity) < int(workshop.workshop.workshop_limit):
            max_attendees = workshop.workshop_room.room_capacity
        else:
            max_attendees = workshop.workshop.workshop_limit
        names = ""
        for name in get_attendees_in_workshop(workshop.workshop_run_id):
            if str(name.order_id) == user_id or admin_mode:
                names = "{} {}, ".format(names, name.first_name.capitalize())

        if workshop.users and len(workshop.users) > 0:
            volunteer = workshop.users[0].first_name
        else:
            volunteer = "None"

        new_workshop = {"workshop_room":workshop.workshop_room.room_name,
                        "workshop_title":workshop.workshop.workshop_title,
                        "workshop_description":workshop.workshop.workshop_description,
                        "workshop_limit":"{} / {}".format(len(get_attendees_in_workshop(workshop.workshop_run_id)), max_attendees),
                        "attendee_names":names,
                        "workshop_id":workshop.workshop_run_id,
                        "volunteer": volunteer,
                        "pilot": workshop.pilot}


        workshop_slots[workshop.slot.slot_id]["workshops"].append(new_workshop)

    for workshop_slot_index, workshop_final_slot in enumerate(workshop_slots):
        workshop_slots[workshop_slot_index]["workshops"] = sorted(workshop_final_slot["workshops"], key=lambda x: x["workshop_room"], reverse=False)

    if not admin_mode:
        workshop_slots = workshop_slots[1:]
    return workshop_slots


def verify_attendee_id(id):
    if id:
        attendees = db_session.query(Attendee).filter(Attendee.order_id == int(id)).all()
        if attendees:
            return attendees
    return False


def get_attendees_in_workshop(workshop_run_id, raw_result=False):
    attendees = db_session.query(RaspberryJamWorkshop, WorkshopAttendee, Workshop, Attendee).filter(RaspberryJamWorkshop.workshop_id == Workshop.workshop_id,
                                                                                                    RaspberryJamWorkshop.workshop_run_id == WorkshopAttendee.workshop_run_id,
                                                                                                    Attendee.attendee_id == WorkshopAttendee.attendee_id,
                                                                                                    RaspberryJamWorkshop.workshop_run_id == workshop_run_id).all()
    if raw_result:
        return attendees
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

    if len(get_attendees_in_workshop(workshop_run_id)) < int(max_attendees):
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


def remove_attendee_to_workshop(jam_id, attendee_id, workshop_run_id):
    booking = db_session.query(WorkshopAttendee).filter(WorkshopAttendee.attendee_id == attendee_id, WorkshopAttendee.workshop_run_id == workshop_run_id).first()
    if booking:
        db_session.delete(booking)
        db_session.commit()
        return True
    return False


def get_users():
    return db_session.query(LoginUser).all()


def get_user_details_from_username(username):
    return db_session.query(LoginUser).filter(LoginUser.username == username).first()


def create_user(username, password_hash, password_salt, first_name, surname, ):
    cookie = LoginCookie()
    db_session.add(cookie)
    db_session.commit()
    user = LoginUser()
    user.username = username
    user.password_hash = password_hash
    user.password_salt = password_salt
    user.first_name = first_name
    user.surname = surname
    user.login_cookie_id = cookie.cookie_id
    user.group_id = 1

    db_session.add(user)
    db_session.commit()


def add_workshop_to_jam_from_catalog(jam_id, workshop_id, volunteer_id, slot_id, room_id, pilot):
    # TODO : Add a whole pile of checks here including if the volunteer is double booked, room is double booked etc.
    workshop = RaspberryJamWorkshop()
    workshop.jam_id = jam_id
    workshop.workshop_id = workshop_id
    workshop.slot_id = slot_id
    workshop.workshop_room_id = room_id
    workshop.pilot = pilot
    if int(volunteer_id) >= 0: # If the None user has been selected, then hit the else
        if workshop.users:
            workshop.users.append(db_session.query(LoginUser).filter(LoginUser.user_id == volunteer_id).first())
        else:
            workshop.users = [db_session.query(LoginUser).filter(LoginUser.user_id == volunteer_id).first(),]
    else:
        workshop.users = []
    db_session.add(workshop)
    db_session.flush()
    db_session.commit()


def remove_workshop_from_jam(workshop_run_id):
    print("Going to delete {}".format(workshop_run_id))
    workshop = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.workshop_run_id == workshop_run_id).first()
    workshop.users = []
    db_session.commit()
    db_session.delete(workshop)

    for attendee in get_attendees_in_workshop(workshop_run_id, raw_result=True):
        db_session.delete(attendee.WorkshopAttendee)

    db_session.commit()


def update_cookie_for_user(user_id):
    new_cookie = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
    current_cookie = db_session.query(LoginUser, LoginCookie).filter(LoginUser.user_id == user_id, LoginUser.login_cookie_id == LoginCookie.cookie_id).one()
    current_cookie.LoginCookie.cookie_value = new_cookie
    db_session.commit()


def get_cookie_for_username(username):
    user = db_session.query(LoginUser, LoginCookie).filter(LoginUser.login_cookie_id == LoginCookie.cookie_id, LoginUser.username == username).first()
    return user.LoginCookie.cookie_value

def get_all_attendees_for_jam(jam_id):
    attendees = db_session.query(Attendee).filter(Attendee.jam_id == jam_id).order_by(Attendee.surname, Attendee.first_name)
    return_attendees = []
    for jam_attendee in attendees:
        return_attendees.append({
            "first_name":jam_attendee.first_name,
            "surname": jam_attendee.surname,
            "order_id": jam_attendee.order_id
        })
    return return_attendees
# TODO : Investigate why jam_attendance isn't being used currently, as need the jam id from it


def database_reset():
    db_session.query(WorkshopAttendee).delete()
    db_session.query(Attendee).delete()
    db_session.commit()


def get_volunteer_data(jam_id, current_user):
    time_slots = db_session.query(WorkshopSlot).all()

    #workshop_data = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.workshop_run_id == WorkshopVolunteer.workshop_run_id,
    #                                                                                 RaspberryJamWorkshop.jam_id == jam_id,
    #                                                                                 ).all()

    u = db_session.query(LoginUser).all()

    workshop_data = db_session.query(RaspberryJamWorkshop).filter(
                                                                                     RaspberryJamWorkshop.jam_id == jam_id,
                                                                                     ).all()


    #d = workshop_data = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.workshop_run_id == WorkshopVolunteer.workshop_run_id,
    #                                                                                 RaspberryJamWorkshop.jam_id == jam_id,
    #                                                                                 WorkshopVolunteer
    #                                                                                 ).all()

    #a = workshop_data.filter(RaspberryJamWorkshop.slot_id == 1).all()

    workshop_rooms_in_use = db_session.query(WorkshopRoom).filter(RaspberryJamWorkshop.workshop_room_id == WorkshopRoom.room_id,
                                                                                        RaspberryJamWorkshop.jam_id == jam_id
                                                                                        ).order_by(WorkshopRoom.room_name).all()

    for time_slot in time_slots:
        time_slot.rooms = []
        for workshop_room in workshop_rooms_in_use:
            room = deepcopy(workshop_room)
            room.workshop = RaspberryJamWorkshop()
            room.workshop.dummy = True
            time_slot.rooms.append(room)
        for workshop in workshop_data:
            for room in time_slot.rooms:
                if room.room_id == workshop.workshop_room_id and time_slot.slot_id == workshop.slot_id:
                    room.workshop = workshop
                    if not room.workshop.workshop_room:
                        room.workshop.bg_colour = grey
                    elif len(room.workshop.users) >= room.workshop.workshop_room.room_volunteers_needed:
                        room.workshop.bg_colour = green
                    elif len(room.workshop.users) >= room.workshop.workshop_room.room_volunteers_needed / 2:
                        room.workshop.bg_colour = yellow
                    elif len(room.workshop.users) == 0:
                        room.workshop.bg_colour = red
                    else:
                        room.workshop.bg_colour = orange

                    if room.workshop in current_user.workshop_runs:
                        room.workshop.signed_up = True
                        room.workshop.bg_colour = blue
                    else:
                        room.workshop.signed_up = False


    return time_slots, sorted(workshop_rooms_in_use, key=lambda x: x.room_name, reverse=False)


def set_user_workshop_runs_from_ids(user, jam_id, workshop_run_ids):
    sessions_block_ids = []
    workshops = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.workshop_run_id.in_(workshop_run_ids), RaspberryJamWorkshop.jam_id == jam_id).all()
    for workshop in workshops: # Verify that the bookings being made don't collide with other bookings by same user for same slot.
        if workshop.slot_id in sessions_block_ids:
            print("Unable to book user in to slot, as they already have a colliding booking for that slot.")
            return False
        sessions_block_ids.append(workshop.slot_id)
    user.workshop_runs = workshops
    db_session.commit()
    return True


def remove_jam(jam_id):
    db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.jam_id == jam_id).delete()
    jam = db_session.query(RaspberryJam).filter(RaspberryJam.jam_id == jam_id).first()
    db_session.delete(jam)
    db_session.commit()


def get_attending_volunteers(jam_id, logged_in_user_id):
    all_volunteers = db_session.query(LoginUser).all() # Get all the volunteers
    for volunteer in all_volunteers:
        volunteer.current_jam_workshops_involved_in = []
        for workshop in volunteer.workshop_runs:
            if workshop.jam_id == jam_id: # Builds the workshops attached to each user
                volunteer.current_jam_workshops_involved_in.append("{}. {}".format(workshop.slot_id, workshop.workshop.workshop_title)) # Builds a list of strings to show in the tooltip
        volunteer.current_jam_workshops_involved_in = sorted(volunteer.current_jam_workshops_involved_in)

    all_volunteers = all_volunteers

    attending = db_session.query(VolunteerAttendance).filter(VolunteerAttendance.jam_id == jam_id).all()
    for attend in attending: # Matches volunteer attendance to users
        for volunteer in all_volunteers:
            if volunteer.user_id == attend.user.user_id:
                volunteer.attend = attend
    return sorted(sorted(all_volunteers, key=lambda x: x.surname, reverse=False), key=lambda x: hasattr(x, "attend"), reverse=True)


def add_volunteer_attendance(jam_id, user_id, attending_jam, attending_setup, attending_packdown, attending_food, notes):
    attendance = db_session.query(VolunteerAttendance).filter(VolunteerAttendance.jam_id == jam_id, VolunteerAttendance.user_id == user_id).first()
    new = False
    if not attendance:
        attendance = VolunteerAttendance()
        new = True
    attendance.user_id = user_id
    attendance.jam_id = jam_id
    attendance.volunteer_attending = attending_jam
    attendance.setup_attending = attending_setup
    attendance.packdown_attending = attending_packdown
    attendance.food_attending = attending_food
    attendance.notes = notes
    if new:
        db_session.add(attendance)
    db_session.commit()


def get_users_not_responded_to_attendance(jam_id):
    all_volunteers = db_session.query(LoginUser).all()
    all_volunteers_responded_attendance = db_session.query(VolunteerAttendance).filter(VolunteerAttendance.jam_id == jam_id).all()
    all_volunteers_responded = []
    for volunteer in all_volunteers_responded_attendance:
        all_volunteers_responded.append(volunteer.user)
    #volunteers_not_responded = all_volunteers - all_volunteers_responded
    volunteers_not_responded = list(set(all_volunteers) - set(all_volunteers_responded))
    return volunteers_not_responded


def delete_workshop(workshop_id):
    workshop = db_session.query(Workshop).filter(Workshop.workshop_id == workshop_id).first()
    db_session.delete(workshop)
    db_session.commit()


def get_user_reset_code(user_id):
    new_code = str(uuid.uuid4()).replace("-", "")[:10]
    user = db_session.query(LoginUser).filter(LoginUser.user_id == user_id).first()
    user.reset_code = new_code
    db_session.commit()
    return new_code


def reset_password(username, reset_code, salt, hash):
    user = db_session.query(LoginUser).filter(LoginUser.username == username, LoginUser.reset_code == reset_code).first()
    if user:
        user.password_hash = hash
        user.password_salt = salt
        user.reset_code = None
        db_session.commit()
        return True
    return False


def set_group_for_user(user_id, group_id):
    user = db_session.query(LoginUser).filter(LoginUser.user_id == user_id).first()
    user.group_id = group_id
    db_session.commit()
