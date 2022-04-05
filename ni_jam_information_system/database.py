import collections
import random
import string
import traceback
import uuid

import os

import math
from typing import Tuple, Any

import misc
from models import *
from eventbrite_interactions import get_eventbrite_attendees_for_event
import datetime
from copy import deepcopy
import configuration
from sqlalchemy import or_, not_, and_, func

red = "#fc9f9f"
orange = "#fcbd00"
yellow = "#fff60a"
green = "#c4fc9f"
grey = "#969696"
blue = "#00bbff"
light_grey = "#ededed"
light_blue = "#00dbc1"
lighter_blue = "#54d1f7"
light_red = "#ffb3b3"


class LoginUserGroupEnum(Enum):
    guest = 1
    attendee = 2
    volunteer = 3
    trustee = 4
    superadmin = 5


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    Base.metadata.create_all(bind=engine)


def first_time_setup():
    init_db()
    if len(db_session.query(Group).all()) == 0:
        db_session.add(Group(group_id=1, group_name="Guest"))
        db_session.add(Group(group_id=2, group_name="Attendee"))
        db_session.add(Group(group_id=3, group_name="Volunteer"))
        db_session.add(Group(group_id=4, group_name="Trustee"))
        db_session.add(Group(group_id=5, group_name="SuperAdmin"))
        db_session.add(EquipmentGroup(equipment_group_id=0, equipment_group_name="Default equipment group"))
        db_session.commit()
        return True
    return False


def convert_to_mysql_datetime(datetime_to_convert: datetime.datetime) -> str:
    f = '%Y-%m-%d %H:%M:%S'
    return datetime_to_convert.strftime(f)


def convert_to_python_datetime(datetime_to_convert: str) -> datetime.datetime:
    f = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.strptime(datetime_to_convert, f)


def get_logged_in_user_object_from_cookie(cookie_value: str) -> LoginUser:
    found_cookie = db_session.query(LoginCookie).filter(LoginCookie.cookie_value == cookie_value).first()
    if found_cookie:
        return found_cookie.user
    return None


def add_standalone_event(event_name, date):
    lowest_usable_event_id = 0
    events = get_jams_in_db()
    for event in events:
        if event.jam_id < 10000:
            if event.jam_id > lowest_usable_event_id:
                lowest_usable_event_id = event.jam_id
                
    event = RaspberryJam(jam_id=lowest_usable_event_id + 1, name=event_name, date=date, event_source=EventSourceEnum.standalone)
    db_session.add(event)
    db_session.commit()


def add_eventbrite_jam(eventbrite_id, jam_name, date):  # Add a new Jam, plus a series of placeholder default hidden workshops (parking, front desk and break time)
    jam = RaspberryJam(jam_id=eventbrite_id, name=jam_name, date=date, event_source=EventSourceEnum.eventbrite)  # Add the Jam row
    db_session.add(jam)
    db_session.commit()
    if configuration.verify_config_item_bool("general", "new_jam_add_default_events"):
        car_parking_workshop = db_session.query(Workshop).filter(Workshop.workshop_title == "Car Parking").first()
        car_parking_room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_name == "Car Park").first()
        car_parking = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=car_parking_workshop.workshop_id, workshop_room_id=car_parking_room.room_id, slot_id=0, pilot=0)
        db_session.add(car_parking)  # Add car parking into slot 0

        front_desk_workshop = db_session.query(Workshop).filter(Workshop.workshop_title == "Front desk").first()
        front_desk_registration_room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_name == "Front Desk Registration").first()
        front_desk_room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_name == "Front Desk General").first()
        front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_registration_room.room_id, slot_id=0, pilot=0)

        db_session.add(front_desk)  # Add front desk registration

        front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_room.room_id, slot_id=1, pilot=0)
        db_session.add(front_desk)
        front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_room.room_id, slot_id=2, pilot=0)
        db_session.add(front_desk)
        front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_room.room_id, slot_id=3, pilot=0)
        db_session.add(front_desk)
        front_desk = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=front_desk_workshop.workshop_id, workshop_room_id=front_desk_room.room_id, slot_id=4, pilot=0)
        db_session.add(front_desk)  # Add 4th normal front desk

        break_room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_name == "Foyer (ground floor)").first()
        break_workshop = db_session.query(Workshop).filter(Workshop.workshop_title == "Break time").first()
        break_time = RaspberryJamWorkshop(jam_id=jam.jam_id, workshop_id=break_workshop.workshop_id, workshop_room_id=break_room.room_id, slot_id=3, pilot=0)
        db_session.add(break_time)  # Add break time into break session

        db_session.commit()


def get_jams_in_db() -> List[RaspberryJam]:
    jams = db_session().query(RaspberryJam).all() 
    return sorted(jams, key=lambda x: x.date, reverse=False)


def add_workshop(workshop_id, workshop_title, workshop_description, workshop_limit, workshop_level, workshop_url, workshop_volunteer_requirements):

    if workshop_id or workshop_id == 0:  # If workshop already exists
        workshop = db_session.query(Workshop).filter(Workshop.workshop_id == workshop_id).first()
        workshop.workshop_title = workshop_title
        workshop.workshop_description = workshop_description
        workshop.workshop_limit = workshop_limit
        workshop.workshop_level = workshop_level
        workshop.workshop_url = workshop_url
        workshop.workshop_volunteer_requirements = workshop_volunteer_requirements
    else:  # If new workshop
        workshop = Workshop(workshop_title=workshop_title, workshop_description=workshop_description, workshop_limit=workshop_limit, workshop_level=workshop_level, workshop_hidden=0, workshop_url=workshop_url, workshop_volunteer_requirements=workshop_volunteer_requirements)
        db_session.add(workshop)
    db_session.commit()


def get_workshops_for_jam_old(jam_id):
    workshops = []
    for workshop in db_session.query(RaspberryJam, RaspberryJamWorkshop, Workshop).filter(RaspberryJam.jam_id == jam_id, RaspberryJamWorkshop.workshop_id == Workshop.workshop_id):
        workshops.append({"workshop_title": workshop.Workshop.workshop_title, "workshop_description": workshop.Workshop.workshop_description, "workshop_level": workshop.Workshop.workshop_level, "workshop_time": workshop.RaspberryJamWorkshop.workshop_time_slot})
    return workshops


def update_single_attendee_check_in_from_eventbrite(event_id, attendee_id, check_in):
    event = get_jam_details(event_id)
    if event.event_source != EventSourceEnum.eventbrite:  # Only import users if it is an Eventbrite event
        return False
    if check_in:
        for attendee in event.attendees:
            if attendee_id == attendee.attendee_id and not attendee.checked_in:
                attendee.checked_in = 1
                attendee.current_location = "Checked in"
                db_session.commit()
                return True
    return False


def update_attendees_from_eventbrite(event_id):
    event = get_jam_details(event_id)
    if event.event_source != EventSourceEnum.eventbrite:  # Only import users if it is an Eventbrite event
        return False
    attendees = get_eventbrite_attendees_for_event(event_id)
    print(f"Number of attendees to import - {len(attendees['attendees'])}")
    for attendee in attendees["attendees"]:

        found_attendee = db_session.query(Attendee).filter(Attendee.attendee_id == int(attendee["id"])).first()

        if attendee["refunded"]:
            if found_attendee:
                db_session.delete(found_attendee)
            continue

        try:
            school = attendee["answers"][2]["answer"]
        except:
            school = None
        if found_attendee:
            new_attendee = found_attendee
        else:
            new_attendee = Attendee()

        new_attendee.attendee_id = int(attendee["id"])
        new_attendee.first_name = attendee["profile"]["first_name"]
        new_attendee.surname = attendee["profile"]["last_name"]
        new_attendee.email_address = "Unknown"
        #if "gender" not in attendee["profile"]:
        #    print("")
        #new_attendee.gender = attendee["profile"]["gender"],
        new_attendee.order_id = int(attendee["order_id"])
        new_attendee.ticket_type = attendee["ticket_class_name"]
        new_attendee.jam_id = int(event_id)
        new_attendee.checked_in = attendee["checked_in"]
        for question in attendee["answers"]:
            if "pinet" in question["question"].lower() and "answer" in question:
                try:  # A slightly unreliable piece of code that can fall over now and then, hence the try/except to stop it breaking main importer.
                    pinet_username = question["answer"].lower().strip().replace(" ", "")
                    if len(pinet_username) >= 3:
                        attendee_login = get_attendee_login(pinet_username)
                        if attendee_login:
                            new_attendee.attendee_login_id = attendee_login.attendee_login_id
                            try:
                                db_session.commit()
                            except:
                                db_session.rollback()
                                raise
                except:
                    traceback.print_exc()
                
            if "age" in question["question"].lower() and "answer" in question: 
                age = question["answer"]
                try:
                    new_attendee.age = int(age)
                except ValueError:
                    print(f"Unable to get age for {new_attendee.first_name} {new_attendee.surname} with id of {new_attendee.first_name} and {age}.")

            if "what level of experience do you see yourself at with raspberry pi?" in question["question"].lower() and "answer" in question:
                answer = question["answer"]
                if "Beginner" in answer:
                    new_attendee.experience_level = "Beginner"
                elif "Intermediate" in answer:
                    new_attendee.experience_level = "Intermediate"
                elif "Expert" in answer:
                    new_attendee.experience_level = "Expert"

        # 4 available states for current_location, Checked in, Checked out, Not arrived and None.
        if new_attendee.current_location is None:  # If current_location has not been set
            if attendee["checked_in"]:
                new_attendee.current_location = "Checked in"
            else:
                new_attendee.current_location = "Not arrived"
        elif new_attendee.current_location == "Not arrived" and attendee["checked_in"]:
            new_attendee.current_location = "Checked in"

        if not found_attendee:
            db_session.add(new_attendee)
    try:
        db_session.commit()
    except:
        db_session.rollback()
        print("Had to rollback import of users...")
        raise
    return True


def get_attendee_login(pinet_username):
    pinet_username = pinet_username.lower()
    attendee_login = db_session.query(AttendeeLogin).filter(AttendeeLogin.attendee_login_name == pinet_username).first()
    return attendee_login


def get_attendees_in_order(order_id, current_jam=False, ignore_parent_tickets=False):
    found_attendees = db_session.query(Attendee).filter(Attendee.order_id == order_id)
    if not found_attendees:
        return None
    else:
        if current_jam:
            found_attendees = found_attendees.filter(Attendee.jam_id == get_current_jam_id())

        if ignore_parent_tickets:
            found_attendees_without_parents = []
            for attendee in found_attendees:
                if not attendee.ticket_type.startswith("Parent"):
                    found_attendees_without_parents.append(attendee)
            return found_attendees_without_parents
        return found_attendees


def get_time_slots_objects():
    slots = db_session.query(WorkshopSlot).order_by(WorkshopSlot.slot_time_start.asc())
    for slot in slots: 
        slot.slot_duration = 0 # TODO: Get slot duration working...
    return slots


def get_volunteers_to_select():
    volunteers = db_session.query(LoginUser).filter(LoginUser.active == 1)
    to_return = []
    for volunteer in volunteers:
        to_return.append((volunteer.user_id, "{} {}".format(volunteer.first_name, volunteer.surname)))
    return to_return


def get_workshops_to_select(show_archived=False):
    workshops = db_session.query(Workshop)
    if show_archived:
        return workshops
    else:
        return workshops.filter((Workshop.workshop_archived == 0) | (Workshop.workshop_archived == None))


def get_workshop_from_workshop_id(workshop_id):
    return db_session.query(Workshop).filter(Workshop.workshop_id == workshop_id).first()


def get_individual_time_slots_to_select():
    to_return = []
    for time_slots in db_session.query(WorkshopSlot).order_by(WorkshopSlot.slot_time_start.asc()):
        to_return.append((time_slots.slot_id, str(time_slots.title)))
    return to_return


def get_workshop_rooms():
    to_return = []
    for workshop_room in db_session.query(WorkshopRoom):
        to_return.append((workshop_room.room_id, workshop_room.room_name))
    return to_return


def get_workshop_rooms_objects():
    rooms = db_session.query(WorkshopRoom)
    return rooms


def get_schedule_by_time_slot(jam_id, order_id, admin=False) -> List[WorkshopSlot]:
    attendee_data = collections.namedtuple('attendee_data', 'attendee bookable message')

    attendees = get_attendees_in_order(order_id).all()
    alerts = get_all_alerts_for_jam(jam_id)

    workshop_slots = db_session.query(WorkshopSlot).all()
    for slot in workshop_slots:
        jam_workshops_in_slot = []
        for workshop in slot.workshops_in_slot:
            if workshop.jam_id == jam_id and (admin or workshop.workshop.workshop_hidden != 1):
                jam_workshops_in_slot.append(workshop)

            # Handle badges
            workshop.potential_attendees = []
            for attendee in attendees:
                bookable = True
                message = ""
                if workshop.workshop.badges:
                    if attendee.attendee_login:
                        for badge in workshop.workshop.badges:
                            if badge not in attendee.attendee_login.attendee_badges:
                                bookable = False
                                message = f"This workshop requires the \"{badge.badge_name}\" badge which you do not have yet. You must have this badge to sign up to this workshop."
                                break
                    else:
                        bookable = False
                        message = "This workshop requires a digital badge and you are not currently logged in with your PiNet username. If you have one, please add it above."
                attendee_data_to_add = attendee_data(attendee=attendee, bookable=bookable, message=message)
                workshop.potential_attendees.append(attendee_data_to_add)

            # Handle alerts
            for alert in alerts:  # TODO : Add all the additional alerts rules
                if alert.slot_id and alert.slot_id == workshop.slot_id:
                    for attendee in workshop.potential_attendees:
                        if alert.ticket_type and alert.ticket_type == attendee.attendee.ticket_type:
                            attendee.attendee.alert = alert

        slot.jam_workshops_in_slot = jam_workshops_in_slot

    return workshop_slots


def verify_attendee_id(attendee_id, jam_id):
    if attendee_id:
        attendees = db_session.query(Attendee).filter(Attendee.order_id == int(attendee_id), Attendee.jam_id == jam_id).all()
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
    if get_if_workshop_has_space(jam_id, workshop_run_id):
        if not str(attendee.ticket_type).startswith("Parent"):
            if not get_if_attendee_booked_in_slot_for_workshop(attendee_id, workshop_run_id):
                workshop_attendee = WorkshopAttendee(attendee_id=attendee_id, workshop_run_id=workshop_run_id)
                db_session.add(workshop_attendee)
                db_session.commit()
                return True, "Success"
            else:
                return False, "{} {} is already booked into another workshop in this slot.".format(attendee.first_name, attendee.surname)
        else:
            return False, "Attempted booking workshop with a Parent ticket, only attendee tickets can be used for booking workshops."
    else:
        return False, "This workshop is already at full capacity, please pick a different workshop."


def remove_attendee_to_workshop(jam_id, attendee_id, workshop_run_id):
    booking = db_session.query(WorkshopAttendee).filter(WorkshopAttendee.attendee_id == attendee_id, WorkshopAttendee.workshop_run_id == workshop_run_id).first()
    if booking:
        db_session.delete(booking)
        db_session.commit()
        return True
    return False


def get_users(include_inactive=False) -> List[LoginUser]:
    users = db_session.query(LoginUser)
    if include_inactive:
        return users.all()
    return users.filter(LoginUser.active == 1).all()


def get_user_details_from_username(username) -> LoginUser:
    return db_session.query(LoginUser).filter(LoginUser.username == username).first()


def get_user_from_cookie(cookie_value) -> LoginUser:
    cookie = db_session.query(LoginCookie).filter(LoginCookie.cookie_value == cookie_value).first()
    if cookie:
        return cookie.user
    return None


def create_user(username, password_hash, password_salt, first_name, surname, email, dob, group_id=1, active=True):
    db_session.commit()
    user = LoginUser()
    user.username = username
    user.password_hash = password_hash
    user.password_salt = password_salt
    user.first_name = first_name
    user.surname = surname
    user.group_id = group_id
    user.email = email
    user.active = active
    user.date_of_birth = dob

    db_session.add(user)
    db_session.commit()


def add_workshop_to_jam_from_catalog(jam_id, workshop_id, volunteer_id, slot_id, room_id, pilot, pair) -> RaspberryJamWorkshop:
    # TODO : Add a whole pile of checks here including if the volunteer is double booked, room is double booked etc.
    workshop = RaspberryJamWorkshop()
    workshop.jam_id = jam_id
    workshop.workshop_id = workshop_id
    workshop.slot_id = slot_id
    workshop.workshop_room_id = room_id
    workshop.pilot = pilot
    workshop.pair = pair
    if int(volunteer_id) >= 0:  # If the None user has been selected, then hit the else
        if workshop.users:
            workshop.users.append(db_session.query(LoginUser).filter(LoginUser.user_id == volunteer_id).first())
        else:
            workshop.users = [db_session.query(LoginUser).filter(LoginUser.user_id == volunteer_id).first(), ]
    else:
        workshop.users = []
    db_session.add(workshop)
    db_session.flush()
    db_session.commit()
    return workshop


def remove_workshop_from_jam(workshop_run_id):
    print("Going to delete {}".format(workshop_run_id))
    workshop = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.workshop_run_id == workshop_run_id).first()
    workshop.users = []
    db_session.commit()
    db_session.delete(workshop)

    for attendee in get_attendees_in_workshop(workshop_run_id, raw_result=True):
        db_session.delete(attendee.WorkshopAttendee)

    db_session.commit()


def get_cookie(cookie_value):
    return db_session.query(LoginCookie).filter(LoginCookie.cookie_value == cookie_value).first()


def new_cookie_for_user(user_id):
    new_cookie_value = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
    new_cookie_expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
    new_cookie = LoginCookie(cookie_value=new_cookie_value, user_id=user_id, cookie_expiry=new_cookie_expiry)
    db_session.add(new_cookie)
    db_session.commit()
    return new_cookie_value


def remove_cookie(cookie_value):
    db_session.query(LoginCookie).filter(LoginCookie.cookie_value == cookie_value).delete()
    db_session.commit()


def update_cookie_expiry(cookie_id):
    cookie = db_session.query(LoginCookie).filter(LoginCookie.cookie_id == cookie_id).first()
    if cookie and cookie.cookie_expiry > datetime.datetime.now():
        cookie.cookie_expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
    db_session.commit()


def get_all_attendees_for_jam(jam_id):
    attendees = db_session.query(Attendee).filter(Attendee.jam_id == jam_id).order_by(Attendee.surname, Attendee.first_name).all()
    return attendees


def database_reset():
    db_session.query(WorkshopAttendee).delete()
    db_session.query(Attendee).delete()
    db_session.commit()


def get_volunteer_data(jam_id, current_user):
    time_slots: List[WorkshopSlot] = db_session.query(WorkshopSlot).order_by(WorkshopSlot.slot_time_start.asc()).all()

    workshop_data: List[RaspberryJamWorkshop] = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.jam_id == jam_id).all()

    workshop_rooms_in_use: List[WorkshopRoom] = db_session.query(WorkshopRoom).filter(RaspberryJamWorkshop.workshop_room_id == WorkshopRoom.room_id,
                                                                  RaspberryJamWorkshop.jam_id == jam_id
                                                                  ).order_by(WorkshopRoom.room_name).all()

    for time_slot in time_slots:
        time_slot.total_volunteers_required = 0
        time_slot.total_volunteers_signed_up = 0
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
                    if room.workshop.workshop_room:  # Room exists
                        if not workshop.workshop.workshop_volunteer_requirements:  # and does not have volunteers needed specified
                            workshop.workshop_needed_volunteers = room.workshop.workshop_room.room_volunteers_needed
                        elif int(workshop.workshop.workshop_volunteer_requirements) < 0:
                            workshop.workshop_needed_volunteers = 0
                        elif int(workshop.workshop.workshop_limit) != 0:  # and does have volunteers specified while also does have attendees able to attend the workshop
                            max_attendees = min(int(workshop.workshop_room.room_capacity), int(workshop.workshop.workshop_limit))
                            volunteers_needed_from_attendees = 1 + (math.ceil(max_attendees / 10) * workshop.workshop.workshop_volunteer_requirements)
                            workshop.workshop_needed_volunteers = max(workshop.workshop_room.room_volunteers_needed, volunteers_needed_from_attendees)  # Set volunteers needed to the calculated figure based on attendees, unless room minimum is greater.
                        else:  # and does not have attendees for the workshop (for example, car parking etc)
                            workshop.workshop_needed_volunteers = workshop.workshop.workshop_volunteer_requirements
                        time_slot.total_volunteers_required = time_slot.total_volunteers_required + workshop.workshop_needed_volunteers
                        time_slot.total_volunteers_signed_up = time_slot.total_volunteers_signed_up + len(workshop.users)

                    if not room.workshop.workshop_room:
                        room.workshop.bg_colour = grey
                    elif len(room.workshop.users) >= workshop.workshop_needed_volunteers:
                        room.workshop.bg_colour = green
                    else:
                        room.workshop.bg_colour = red

                    if room.workshop in current_user.workshop_runs:
                        room.workshop.signed_up = True
                        room.workshop.bg_colour = blue
                    else:
                        room.workshop.signed_up = False

    return time_slots, sorted(workshop_rooms_in_use, key=lambda x: x.room_name, reverse=False)


def get_workshop_timetable_data(jam_id, include_hidden_time_slots=False) -> Tuple[List[WorkshopSlot], List[WorkshopRoom]]:  # Similar to get_volunteer_data(), but for the large TV with different colouring.
    if include_hidden_time_slots:
        time_slots = db_session.query(WorkshopSlot).order_by(WorkshopSlot.slot_time_start.asc()).all()
    else:
        time_slots = db_session.query(WorkshopSlot).filter(WorkshopSlot.slot_hidden == False).order_by(WorkshopSlot.slot_time_start.asc()).all()

    workshop_data = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.jam_id == jam_id, RaspberryJamWorkshop.workshop_id == Workshop.workshop_id, Workshop.workshop_hidden != 1).all()

    workshop_rooms_in_use = db_session.query(WorkshopRoom).filter(RaspberryJamWorkshop.workshop_room_id == WorkshopRoom.room_id,
                                                                  RaspberryJamWorkshop.jam_id == jam_id,
                                                                  RaspberryJamWorkshop.workshop_id == Workshop.workshop_id,
                                                                  Workshop.workshop_hidden != 1
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
                    elif room.workshop.workshop.workshop_level == "Beginner":
                        room.workshop.bg_colour = green
                    elif room.workshop.workshop.workshop_level == "Intermediate":
                        room.workshop.bg_colour = orange
                    elif room.workshop.workshop.workshop_level == "Advanced":
                        room.workshop.bg_colour = red
                    elif room.workshop.workshop.workshop_level == "Not taught":
                        room.workshop.bg_colour = light_blue

    return time_slots, sorted(workshop_rooms_in_use, key=lambda x: x.room_name, reverse=False)


def set_user_workshop_runs_from_ids(user, jam_id, workshop_run_ids):
    sessions_block_ids = []
    workshops = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.workshop_run_id.in_(workshop_run_ids), RaspberryJamWorkshop.jam_id == jam_id).all()
    for workshop in workshops:  # Verify that the bookings being made don't collide with other bookings by same user for same slot.
        if workshop.slot_id in sessions_block_ids:
            print("Unable to book user in to slot, as they already have a colliding booking for that slot.")
            return False
        sessions_block_ids.append(workshop.slot_id)
    user.workshop_runs = workshops
    db_session.commit()
    return True


def remove_jam(jam_id):
    workshops = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.jam_id == jam_id).all()
    for workshop in workshops:
        workshop.users = []
    db_session.commit()

    for workshop in workshops:
        db_session.delete(workshop)

    db_session.query(Attendee).filter(Attendee.jam_id == jam_id).delete()
    jam = db_session.query(RaspberryJam).filter(RaspberryJam.jam_id == jam_id).first()
    db_session.delete(jam)
    db_session.commit()


def select_jam(jam_id):
    config_option = db_session.query(Configuration).filter(Configuration.config_name == "jam_id").first()
    if config_option:
        config_option.config_value = str(jam_id)
    else:
        db_session.add(Configuration(config_name="jam_id", config_value=jam_id))
    db_session.commit()


def get_attending_volunteers(jam_id, only_attending_volunteers=False) -> Tuple[List[LoginUser], Any]:  # Get all the volunteers
    if only_attending_volunteers:
        attending_volunteers = db_session.query(VolunteerAttendance).filter(VolunteerAttendance.jam_id == jam_id,
                                                                            VolunteerAttendance.volunteer_attending).all()
        all_volunteers = []
        for user in attending_volunteers:
            all_volunteers.append(user.user)
    else:
        all_volunteers = get_users()
    for volunteer in all_volunteers:
        volunteer.current_jam_workshops_involved_in = []
        for workshop in volunteer.workshop_runs:
            if workshop.jam_id == jam_id:  # Builds the workshops attached to each user
                volunteer.current_jam_workshops_involved_in.append("{}. {}".format(workshop.slot_id, workshop.workshop.workshop_title))  # Builds a list of strings to show in the tooltip
        volunteer.current_jam_workshops_involved_in = sorted(volunteer.current_jam_workshops_involved_in)

    all_volunteers = all_volunteers
    Stats = collections.namedtuple("Stats", "attending_main_jam attending_setup attending_packdown attending_food")
    stats = Stats([], [], [], [])
    attending : List[VolunteerAttendance] = db_session.query(VolunteerAttendance).filter(VolunteerAttendance.jam_id == jam_id).all()
    for attend in attending:  # Matches volunteer attendance to users
        for volunteer in all_volunteers:
            if volunteer.user_id == attend.user.user_id:
                volunteer.attend = attend
                if volunteer.attend.volunteer_attending:
                    stats.attending_main_jam.append(volunteer)
                if volunteer.attend.setup_attending:
                    stats.attending_setup.append(volunteer)
                if volunteer.attend.packdown_attending:
                    stats.attending_packdown.append(volunteer)
                if volunteer.attend.food_attending:
                    stats.attending_food.append(volunteer)
                
    sorted_volunteers = sorted(sorted(all_volunteers, key=lambda x: x.surname, reverse=False), key=lambda x: bool(x.attend), reverse=True)
    return sorted_volunteers, stats


def add_volunteer_attendance(jam_id, user_id, attending_jam, attending_setup, attending_packdown, attending_food, notes, arrival_time):
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
    attendance.current_location = "Not arrived"
    attendance.last_edit_date = func.current_timestamp()
    attendance.arrival_time = arrival_time
    if new:
        db_session.add(attendance)
    db_session.commit()


def get_users_not_responded_to_attendance(jam_id):
    all_volunteers = db_session.query(LoginUser).filter(LoginUser.active).all()
    all_volunteers_responded_attendance = db_session.query(VolunteerAttendance).filter(VolunteerAttendance.jam_id == jam_id).all()
    all_volunteers_responded = []
    for volunteer in all_volunteers_responded_attendance:
        all_volunteers_responded.append(volunteer.user)
    volunteers_not_responded = list(set(all_volunteers) - set(all_volunteers_responded))
    return volunteers_not_responded


def delete_workshop(workshop_id):
    workshop = db_session.query(Workshop).filter(Workshop.workshop_id == workshop_id).first()
    db_session.delete(workshop)
    db_session.commit()


def archive_workshop(workshop_id):
    workshop = db_session.query(Workshop).filter(Workshop.workshop_id == workshop_id).first()
    workshop.workshop_archived = 1
    db_session.commit()


def get_user_reset_code(user_id):
    new_code = str(uuid.uuid4()).replace("-", "")[:10]
    user = db_session.query(LoginUser).filter(LoginUser.user_id == user_id).first()
    user.reset_code = new_code
    db_session.commit()
    return new_code


def reset_password(user, salt, hash):
    if user:
        user.password_hash = hash
        user.password_salt = salt
        user.reset_code = None
        user.forgotten_password_expiry = datetime.datetime.now()
        db_session.commit()
        return True
    return False


def set_group_for_user(user_id, group_id):
    user = db_session.query(LoginUser).filter(LoginUser.user_id == user_id).first()
    user.group_id = group_id
    db_session.commit()


def get_current_jam_id():
    jam = db_session.query(Configuration).filter(Configuration.config_name == "jam_id").first()
    if jam:
        return int(jam.config_value)
    return 0


def check_out_attendee(attendee_id):
    if len(attendee_id) < 6:  # Check if volunteer
        volunteer_attendance = db_session.query(VolunteerAttendance).join(LoginUser).filter_by(user_id=attendee_id).filter(VolunteerAttendance.jam_id == get_current_jam_id()).first()
        volunteer_attendance.current_location = "Checked out"
    else:
        attendee = db_session.query(Attendee).filter(Attendee.attendee_id == attendee_id).first()
        attendee.current_location = "Checked out"
    db_session.commit()


def check_in_attendee(attendee_id):
    if len(attendee_id) < 6:  # Check if volunteer
        volunteer_attendance = db_session.query(VolunteerAttendance).join(LoginUser).filter_by(user_id=attendee_id).filter(VolunteerAttendance.jam_id == get_current_jam_id()).first()
        volunteer_attendance.current_location = "Checked in"
    else:
        attendee = db_session.query(Attendee).filter(Attendee.attendee_id == attendee_id).first()
        attendee.current_location = "Checked in"
    db_session.commit()


def get_jam_details(jam_id):
    jam = db_session.query(RaspberryJam).filter(RaspberryJam.jam_id == jam_id).first()
    if jam:
        return jam
    return RaspberryJam(name="*** No Jam selected - Please select one from Add Jam ***", date=datetime.datetime.now())


def remove_workshop_file(file_id):
    file = db_session.query(WorkshopFile).filter(WorkshopFile.file_id == file_id).first()
    workshop_id = file.workshop_id
    db_session.delete(file)
    db_session.commit()
    os.remove(file.file_path)
    return workshop_id


def add_workshop_file(file_title, file_path, file_permission, file_type, workshop_id):
    if db_session.query(WorkshopFile).filter(WorkshopFile.workshop_id == workshop_id, WorkshopFile.file_path == file_path).first():  # If file of same name already exists
        return False
    file = WorkshopFile(file_title=file_title, file_path=file_path, file_permission=file_permission, workshop_id=workshop_id, file_edit_date=datetime.datetime.now(), file_type=file_type)
    db_session.add(file)
    db_session.commit()
    return True


def get_file_for_download(workshop_id, file_path):
    file = db_session.query(WorkshopFile).filter(WorkshopFile.workshop_id == workshop_id, WorkshopFile.file_path == file_path).first()
    return file


def get_workshop_run(workshop_run_id):
    workshop_run = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.workshop_run_id == workshop_run_id).first()
    return workshop_run


def get_inventories():
    inventories = db_session.query(Inventory).all()
    return inventories


def add_inventory(inventory_title):
    if db_session.query(Inventory).filter(Inventory.inventory_title == inventory_title).all():
        return False
    inventory = Inventory(inventory_title=inventory_title, inventory_date=datetime.datetime.now())
    db_session.add(inventory)
    db_session.commit()
    return True


def set_configuration_item(configuration_key, configuration_value):
    current_configuration_items = db_session.query(Configuration).filter(Configuration.config_name == configuration_key)
    if current_configuration_items:
        for item in current_configuration_items:
            db_session.delete(item)
    new_configuration = Configuration(config_name=configuration_key, config_value=configuration_value)
    db_session.add(new_configuration)
    db_session.commit()


def get_configuration_item(configuration_key):
    current_configuration_item = db_session.query(Configuration).filter(Configuration.config_name == configuration_key).first()
    if current_configuration_item:
        return current_configuration_item.config_value
    return None


def get_equipment_in_inventory(inventory_id):
    equipment_entries = db_session.query(EquipmentEntry).filter(InventoryEquipmentEntry.inventory_id == inventory_id,
                                                   Equipment.equipment_id == EquipmentEntry.equipment_id,  # Link the tables up
                                                   EquipmentEntry.equipment_entry_id == InventoryEquipmentEntry.equipment_entry_id).all()  # Link the tables up
    equipment = []
    for equipment_entry in equipment_entries:
        if equipment_entry.attached_equipment not in equipment:
            equipment_entry.attached_equipment.equipment_entries = []
            equipment.append(equipment_entry.attached_equipment)
        equipment_entry.attached_equipment.equipment_entries.append(equipment_entry)

    for single_equipment in equipment:  # Add quantities on to individual entries
        single_equipment.total_quantity = 0
        for equipment_entry in single_equipment.equipment_entries:
            for inventory in equipment_entry.equipment_inventories:
                if inventory.inventory_id == inventory_id:
                    equipment_entry.equipment_quantity = inventory.entry_quantity
                    single_equipment.total_quantity += inventory.entry_quantity

    return equipment


def get_all_equipment(manual_add_only=False):
    """
    :param manual_add_only: If is set for manual adding, don't return any equipment that has multiple entries in the system
    """
    if manual_add_only:
        equipment = db_session.query(Equipment).filter(or_(and_(EquipmentEntry.equipment_entry_number == -1, Equipment.equipment_id == EquipmentEntry.equipment_id), not_(Equipment.equipment_entries.any())))

    else:
        equipment = db_session.query(Equipment)

    return equipment


def get_all_equipment_for_workshop(workshop_id):
    current_inventory = get_configuration_item("current_inventory")
    if current_inventory:
        #equipment = db_session.query(WorkshopEquipment).filter(Equipment.equipment_id == WorkshopEquipment.equipment_id, 
        #                                                       WorkshopEquipment.workshop_id == workshop_id,
        #                                                       funcfilter(func.sum(InventoryEquipmentEntry).label("total"), InventoryEquipmentEntry.inventory_id == current_inventory, InventoryEquipmentEntry.equipment_entry.equipment_id == Equipment.equipment_id)
        #                                                       ).all()
        # TODO : Someday ideally the query above would be finished, to count the amount of a piece of equipment total and include it with the returned equipment
        equipment = db_session.query(WorkshopEquipment).filter(Equipment.equipment_id == WorkshopEquipment.equipment_id, WorkshopEquipment.workshop_id == workshop_id).all() # Temporary
    else:
        equipment = db_session.query(WorkshopEquipment).filter(Equipment.equipment_id == WorkshopEquipment.equipment_id, WorkshopEquipment.workshop_id == workshop_id).all()
    return equipment


def remove_workshop_equipment(equipment_id, workshop_id):
    workshop_equipment = db_session.query(WorkshopEquipment).filter(WorkshopEquipment.workshop_id == workshop_id, WorkshopEquipment.equipment_id == equipment_id).first()
    db_session.delete(workshop_equipment)
    db_session.commit()


def get_equipment_groups():
    equipment_groups = db_session.query(EquipmentGroup)
    return equipment_groups


def get_equipment_by_id(equipment_id):
    single_equipment = db_session.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    return single_equipment


def add_equipment_to_workshop(equipment_id, workshop_id, equipment_quantity, per_attendee):
    db_session.add(WorkshopEquipment(equipment_id=equipment_id, workshop_id=workshop_id, equipment_per_attendee=per_attendee, equipment_quantity=equipment_quantity))
    db_session.commit()


def add_equipment_entries(equipment_id, quantity):
    return_nums = []
    equipment = get_equipment_by_id(equipment_id)
    start_number = 0
    if equipment.equipment_entries:
        start_number = equipment.equipment_entries[-1].equipment_entry_number + 1
    for num in range(0, quantity):
        new_entry = EquipmentEntry(equipment_id=equipment_id, equipment_entry_number=start_number+num)
        db_session.add(new_entry)
        db_session.flush()
        return_nums.append([new_entry.equipment_entry_id, equipment.equipment_code + str(start_number+num).zfill(3)])
    db_session.commit()
    return return_nums


def add_equipment(equipment_name, equipment_code, equipment_group_id):
    if db_session.query(Equipment).filter(Equipment.equipment_name == equipment_name).first():  # Check equipment with same title doesn't already exist
        return False
    if db_session.query(Equipment).filter(Equipment.equipment_code == equipment_code).first():  # Check equipment with same code doesn't already exist
        return False
    db_session.add(Equipment(equipment_name=equipment_name, equipment_code=equipment_code, equipment_group_id=equipment_group_id))
    db_session.commit()
    return True


def add_equipment_quantity_to_inventory(inventory_id, equipment_id, entry_quantity):
    found_first_inventory_equipment = db_session.query(InventoryEquipmentEntry).filter(Equipment.equipment_id == equipment_id, 
                                                                                       EquipmentEntry.equipment_id == Equipment.equipment_id,
                                                                                       EquipmentEntry.equipment_entry_id == InventoryEquipmentEntry.equipment_entry_id,
                                                                                       InventoryEquipmentEntry.inventory_id == inventory_id
                                                                                       ).first()
    if found_first_inventory_equipment:
        found_first_inventory_equipment.entry_quantity = entry_quantity
    else:
        new_equipment_entry = EquipmentEntry(equipment_id=equipment_id, equipment_entry_number=-1)
        db_session.add(new_equipment_entry)
        db_session.flush()
        db_session.add(InventoryEquipmentEntry(inventory_id=inventory_id, equipment_entry_id=new_equipment_entry.equipment_entry_id, entry_quantity=entry_quantity))
    db_session.commit()
    return True


def add_equipment_entry_to_inventory(inventory_id, equipment_entry_id, entry_quantity):
    found_entry = db_session.query(InventoryEquipmentEntry).filter(InventoryEquipmentEntry.inventory_id == inventory_id, InventoryEquipmentEntry.equipment_entry_id == equipment_entry_id).first()
    if found_entry:
        found_entry.entry_quantity = entry_quantity
    else:
        db_session.add(InventoryEquipmentEntry(equipment_entry_id=equipment_entry_id, inventory_id=inventory_id, entry_quantity=entry_quantity))
    db_session.commit()
    return True


def remove_equipment_entry_to_inventory(inventory_id, equipment_entry_id):
    found_inventory_entry = db_session.query(InventoryEquipmentEntry).filter(InventoryEquipmentEntry.inventory_id == inventory_id, InventoryEquipmentEntry.equipment_entry_id == equipment_entry_id).first()
    if found_inventory_entry:
        db_session.delete(found_inventory_entry)
        db_session.commit()


def get_wrangler_overview(jam_id):
    sessions_data = db_session.query(WorkshopSlot).filter(RaspberryJamWorkshop.jam_id == jam_id).order_by(WorkshopSlot.slot_time_start.asc())
    return sessions_data


def enable_user(user_id, enable):
    user = db_session.query(LoginUser).filter(LoginUser.user_id == user_id).first()
    user.active = enable
    db_session.commit()


def add_slot(slot_id, slot_time_start, slot_time_end, slot_name):
    if slot_id or slot_id == 0:  # Already existing slot
        slot = db_session.query(WorkshopSlot).filter(WorkshopSlot.slot_id == slot_id).first()
    else:  # New slot
        slot = WorkshopSlot()
    slot.slot_time_start = slot_time_start
    slot.slot_time_end = slot_time_end
    slot.slot_hidden = False
    slot.slot_name = slot_name
    db_session.add(slot)
    db_session.commit()


def remove_slot(slot_id):
    slot = db_session.query(WorkshopSlot).filter(WorkshopSlot.slot_id == int(slot_id)).first()
    db_session.delete(slot)
    db_session.commit()


def add_workshop_room(room_id, room_name, room_capacity, room_volunteers_needed):
    if room_id or room_id == 0:
        room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_id == room_id).first()
    else:
        if db_session.query(WorkshopRoom).filter(WorkshopRoom.room_name == room_name).all():
            return False
        room = WorkshopRoom()
    room.room_name = room_name
    room.room_capacity = room_capacity
    room.room_volunteers_needed = room_volunteers_needed
    db_session.add(room)
    db_session.commit()
    return True


def remove_room(room_id):
    room = db_session.query(WorkshopRoom).filter(WorkshopRoom.room_id == int(room_id)).first()
    db_session.delete(room)
    db_session.commit()


def get_all_badges(include_hidden=False):
    badges = db_session.query(BadgeLibrary)
    if include_hidden:
        return badges
    else:
        return badges.filter((BadgeLibrary.badge_hidden == 0) | (BadgeLibrary.badge_hidden == None))


def add_badge(badge_id, badge_name, badge_description, badge_required_non_core_count, badge_hidden=False):
    if badge_id == -1 or not db_session.query(BadgeLibrary).filter(BadgeLibrary.badge_id == badge_id).first():  # New badge
        badge = BadgeLibrary(badge_name=badge_name, badge_description=badge_description, badge_hidden=badge_hidden, badge_children_required_count=int(badge_required_non_core_count))
        db_session.add(badge)
    else:
        badge = db_session.query(BadgeLibrary).filter(BadgeLibrary.badge_id == badge_id).first()
        badge.badge_id = int(badge_id)
        badge.badge_name = badge_name
        badge.badge_description = badge_description
        badge.badge_hidden=badge_hidden
        badge.badge_children_required_count = int(badge_required_non_core_count)

    db_session.commit()


def get_badge(badge_id) -> BadgeLibrary:
    badge = db_session.query(BadgeLibrary).filter(BadgeLibrary.badge_id == badge_id).first()
    return badge


def get_all_dependent_badges(badge_id):
    dependent_badges = db_session.query(BadgeDependencies).filter(BadgeDependencies.parent_badge_id == badge_id).all()
    return dependent_badges


def add_badge_dependency(badge_id, dependent_badge_id, badge_awarded_core):
    if db_session.query(BadgeDependencies).filter(BadgeDependencies.parent_badge_id == int(badge_id), BadgeDependencies.dependency_badge_id == int(dependent_badge_id)).first():
        return False  # Badge dependency already exists
    badge_dependency = BadgeDependencies(parent_badge_id=badge_id, dependency_badge_id=dependent_badge_id, badge_awarded_core=badge_awarded_core)
    db_session.add(badge_dependency)
    db_session.commit()
    return True


def remove_badge_workshop_requirement(workshop_id, badge_id):
    badge_requirement = db_session.query(WorkshopBadge).filter(WorkshopBadge.workshop_id == workshop_id, WorkshopBadge.badge_id == badge_id).first()
    db_session.delete(badge_requirement)
    db_session.commit()


def add_badge_to_workshop(workshop_id, badge_id):
    workshop_badge = WorkshopBadge(workshop_id=workshop_id, badge_id=badge_id)
    db_session.add(workshop_badge)
    db_session.commit()


def remove_badge_dependency(badge_id, dependency_badge_id):
    badge_dependency = db_session.query(BadgeDependencies).filter(BadgeDependencies.parent_badge_id == badge_id, BadgeDependencies.dependency_badge_id == dependency_badge_id).first()
    db_session.delete(badge_dependency)
    db_session.commit()


def get_all_trustees():
    trustees = db_session.query(LoginUser).filter(LoginUser.group_id >= 4).all()
    return trustees


def _get_child_badges(badge:BadgeLibrary, total_badges):
    if badge and badge.dependent_badges:
        for b in badge.badge_dependencies:
            total_badges.append(b.dependency_badge)
            total_badges = total_badges + _get_child_badges(b.dependency_badge, [])
    return total_badges


def get_badges_needed_for_workshop(workshop_id):
    workshop = db_session.query(Workshop).filter(Workshop.workshop_id == workshop_id).first()
    badges = set()
    for badge in workshop.badges:
        badges.add(badge)
        badges = badges.union(set(_get_child_badges(badge, [])))


def get_workshop_badge_requirements_fulfilled(workshop:Workshop, attendee:AttendeeLogin):
    if not attendee and workshop.badges:
        return "Disabled", "No PiNet username attached"
    for b in workshop.badges:
        if b not in attendee.attendee_badges:
            return "Disabled", f"Missing badge {b.badge_name}"
    return "", ""


def get_attendee_login_from_attendee_id(attendee_id):
    attendee = db_session.query(Attendee).filter(Attendee.attendee_id == attendee_id).first()
    return attendee.attendee_login


def get_attendee_from_attendee_id(attendee_id):
    attendee = db_session.query(Attendee).filter(Attendee.attendee_id == attendee_id).first()
    return attendee


def get_all_alerts_for_jam(jam_id) -> List[AlertConfig]:
    alerts = db_session.query(AlertConfig).filter(or_(AlertConfig.jam_id == None, AlertConfig.jam_id == jam_id)).all()
    return alerts


def update_pinet_username_from_attendee_id(attendee_id, pinet_username):
    attendee = db_session.query(Attendee).filter(Attendee.attendee_id == int(attendee_id)).first()
    attendee_login = db_session.query(AttendeeLogin).filter(AttendeeLogin.attendee_login_name == pinet_username.lower()).first()
    if attendee:
        if attendee.attendee_login_id:
            if not pinet_username.strip() or " " in pinet_username.strip(): # If a blank username is submitted or spaces in the name
                return False
            attendee.attendee_login.attendee_login_name = pinet_username.lower().strip()
        elif attendee_login:
            attendee.attendee_login = attendee_login
        else:  # If the attendee_login hasn't been found in the system
            return False
        db_session.commit()
        return attendee.attendee_login
    return False


def add_pinet_usernames(pinet_usernames):
    attendee_logins = get_attendee_logins()
    new_accounts = []
    for pinet_username in pinet_usernames:
        for attendee_login in attendee_logins:
            pinet_username = pinet_username.lower().strip().replace(" ", "")
            if attendee_login.attendee_login_name == pinet_username:
                break
        else:
            new_accounts.append(pinet_username)

    for account in new_accounts:
        print(f"Adding PiNet username {account}.")
        new_attendee_login = AttendeeLogin(attendee_login_name=account)
        db_session.add(new_attendee_login)

    db_session.commit()


def verify_all_workshop_badges_exist():
    workshops = db_session.query(Workshop).filter(Workshop.workshop_badge == None).all()
    for workshop in workshops:
        badge = BadgeLibrary(badge_name=f"workshop_{workshop.workshop_title.replace(' ', '_')}", badge_description=f"Automatically created badge for {workshop.workshop_title} workshop.", badge_hidden=True, badge_children_required_count=0, workshop_id=workshop.workshop_id)
        print(f"Adding badge for workshop {workshop.workshop_title}.")
        db_session.add(badge)
    db_session.commit()


def update_workshop_badge_award(attendee_login: AttendeeLogin, badge_id):
    if attendee_login:
        badge = db_session.query(AttendeeLoginBadges).filter(AttendeeLoginBadges.attendee_login_id == attendee_login.attendee_login_id, AttendeeLoginBadges.badge_id == int(badge_id)).first()
        if badge:
            db_session.delete(badge) # If badge is already in the system, remove it
        else:
            db_session.add(AttendeeLoginBadges(attendee_login_id=attendee_login.attendee_login_id, badge_id=int(badge_id), badge_award_date=datetime.datetime.now()))
        db_session.commit()
        update_badges_for_attendee(attendee_login=attendee_login)
        return True


def update_badges_for_attendee(attendee_id=None, attendee=None, attendee_login=None): 
    # Iterate through all possible badges and verify if the user is due to be awarded them.

    if not attendee and not attendee_login:
        attendee = db_session.query(Attendee).filter(Attendee.attendee_id == attendee_id).first()
    if attendee:
        attendee_login = attendee.attendee_login

    if attendee_login:
        if attendee_login:
            potential_badges_to_award = True
            while potential_badges_to_award:
                attendee_badges = attendee_login.attendee_badges
                badges: List[BadgeLibrary] = db_session.query(BadgeLibrary).filter(BadgeLibrary.badge_hidden == False).all()
                potential_badges_to_award = False
                for badge in badges:
                    if badge in attendee_badges:  # If attendee already has the badge
                        continue
                    if not badge.dependent_badges:  # If badge has no dependencies
                        continue
                    has_deps = True
                    non_core_deps = 0
                    for badge_dependency in badge.badge_dependencies:
                        if badge_dependency.badge_awarded_core:
                            if badge_dependency.dependency_badge not in attendee_badges:
                                has_deps = False
                                break  # Don't award badge as they are missing a core badge
                        else:
                            if badge_dependency.dependency_badge in attendee_badges:
                                non_core_deps = non_core_deps + 1
                    if has_deps and non_core_deps >= badge.badge_children_required_count:
                        potential_badges_to_award = True
                        print(f"Awarding {badge.badge_name} to {attendee_login.attendee_login_name}.")
                        db_session.add(AttendeeLoginBadges(attendee_login_id=attendee_login.attendee_login_id, badge_id=int(badge.badge_id), badge_award_date=datetime.datetime.now()))
                        db_session.commit()


def update_badges_for_all_attendees():
    completed_attendee_logins = []
    attendees = db_session.query(Attendee)
    for attendee in attendees:
        if attendee.attendee_login:
            if attendee.attendee_login not in completed_attendee_logins:
                update_badges_for_attendee(None, attendee)
                completed_attendee_logins.append(attendee.attendee_login)
    return True


def get_attendee_login_from_attendee_login_id(attendee_login_id) -> AttendeeLogin:
    attendee_login = db_session.query(AttendeeLogin).filter(AttendeeLogin.attendee_login_id == attendee_login_id).first()
    return attendee_login


def get_attendee_logins() -> List[AttendeeLogin]:
    attendee_logins = db_session.query(AttendeeLogin).all()
    return attendee_logins


def get_all_workshop_bookings_count():
    return db_session.query(WorkshopAttendee).count()


def get_all_attendees_count():
    return db_session.query(Attendee).count()


def get_login_users(include_archived=False) -> List[LoginUser]:
    login_users = db_session.query(LoginUser)
    if not include_archived:
        login_users = login_users.filter(LoginUser.active)
    return login_users.all()


def get_login_user_from_user_id(user_id) -> LoginUser:
    user = db_session.query(LoginUser).filter(LoginUser.user_id == user_id).first()
    return user


def set_jam_password(jam_id, password):
    jam = db_session.query(RaspberryJam).filter(RaspberryJam.jam_id == int(jam_id)).first()
    if password == "None" or not password:
        password = None
    jam.jam_password = password
    db_session.commit()


def get_jam_password(jam_id=None):
    if not jam_id:
        jam_id = get_current_jam_id()
    jam_password = get_jam_details(jam_id).jam_password
    return jam_password


def get_eventbrite_webhook_key():
    key_value = db_session.query(Configuration).filter(Configuration.config_name == "eventbrite_webhook_key").first()
    if key_value:
        return key_value.config_value
    return None


def get_login_user_from_email(email_address) -> LoginUser:
    return db_session.query(LoginUser).filter(LoginUser.email == email_address).first()


def get_user_from_password_reset_url(password_reset_url):
    return db_session.query(LoginUser).filter(LoginUser.forgotten_password_url == password_reset_url).first()


def verify_password_reset_url(reset_key):
    if len(str(reset_key)) == 64:
        user = db_session.query(LoginUser).filter(LoginUser.forgotten_password_url == reset_key).first()
        if user:
            if user.forgotten_password_expiry > datetime.datetime.now():
                return True
    return False


def generate_password_reset_url(user_ud) -> LoginUser:
    user = db_session.query(LoginUser).filter(LoginUser.user_id == user_ud).first()
    user.forgotten_password_url = str(uuid.uuid4()).replace("-", "") + str(uuid.uuid4()).replace("-", "")
    user.forgotten_password_expiry = datetime.datetime.now() + datetime.timedelta(days=2)
    db_session.commit()
    return user


def get_all_police_checks() -> List[PoliceCheck]:
    police_checks = db_session.query(PoliceCheck).order_by(PoliceCheck.certificate_application_date).all()
    return police_checks


def get_police_checks_for_user(user_id):
    police_checks = db_session.query(PoliceCheck).filter(PoliceCheck.user_id == user_id).all()
    return police_checks


def get_police_check_single(user_id, certificate_table_id) -> PoliceCheck:
    police_check = db_session.query(PoliceCheck).filter(PoliceCheck.user_id == user_id, PoliceCheck.certificate_table_id == certificate_table_id).first()
    return police_check


def update_police_check(user: LoginUser, certificate_table_id, certificate_type, certificate_application_date, certificate_reference, certificate_issue_date, certificate_expiry_date):
    police_check: PoliceCheck = db_session.query(PoliceCheck).filter(PoliceCheck.certificate_table_id == certificate_table_id).first()
    if police_check:
        if police_check.user_id != user.user_id:
            return False
    else:
        police_check = PoliceCheck()

    police_check.user_id = user.user_id
    police_check.certificate_type = str(certificate_type)
    police_check.certificate_application_date = certificate_application_date
    police_check.certificate_reference = certificate_reference
    police_check.certificate_issue_date = certificate_issue_date
    police_check.certificate_expiry_date = certificate_expiry_date
    police_check.certificate_update_service_safe = False
    db_session.add(police_check)
    db_session.commit()
    if certificate_type == CertificateTypeEnum.DBS_Update_Service.value and certificate_reference and certificate_issue_date and certificate_expiry_date:
        verify_dbs_update_service_certificate(user, police_check.certificate_table_id)


def verify_dbs_update_service_certificate(user: LoginUser, certificate_table_id):
    raw_cert = db_session.query(PoliceCheck).filter(PoliceCheck.certificate_table_id == certificate_table_id)
    cert: PoliceCheck = raw_cert.first()

    if cert and cert.user.date_of_birth and (cert.user_id == user.user_id or user.group.group_id >= LoginUserGroupEnum.trustee):
        dbs_response = misc.check_dbs_certificate(cert.certificate_reference, cert.user.surname, cert.user.date_of_birth, user.first_name, user.surname, configuration.verify_config_item("general", "jam_organisation_name"))
        cert.certificate_last_digital_checked = datetime.datetime.now()
        if dbs_response:
            cert.certificate_update_service_safe = True
        else:
            cert.certificate_update_service_safe = False
        db_session.add(cert)
        db_session.commit()


def confirm_police_certificate_verified(user_id, certificate_table_id):
    trustee: LoginUser = db_session.query(LoginUser).filter(LoginUser.user_id == user_id, LoginUser.group_id >= LoginUserGroupEnum.trustee).first()
    if trustee:
        cert: PoliceCheck = db_session.query(PoliceCheck).filter(PoliceCheck.certificate_table_id == certificate_table_id).first()
        if cert:
            cert.verified_in_person_by_user = trustee.user_id
            cert.certificate_in_person_verified_on = datetime.datetime.now()
            db_session.commit()


def update_login_user_date_of_birth(user: LoginUser, date_of_birth):
    user.date_of_birth = date_of_birth
    db_session.add(user)
    db_session.commit()


def remove_police_check(user: LoginUser, certificate_table_id):
    cert = db_session.query(PoliceCheck).filter(PoliceCheck.certificate_table_id == certificate_table_id, PoliceCheck.user_id == user.user_id).first()
    if cert:
        db_session.delete(cert)
        db_session.commit()
        return True
    return False

def get_user_from_ics_uuid(ics_uuid) -> LoginUser:
    user = db_session.query(LoginUser).filter(LoginUser.ics_uuid == ics_uuid).first()
    return user


def get_volunteer_signup_workshops_for_jam(jam_id, login_user:LoginUser) -> List[RaspberryJamWorkshop]:
    if jam_id:
        workshops = db_session.query(RaspberryJamWorkshop).filter(RaspberryJamWorkshop.jam_id == jam_id).all()
    else:
        workshops = db_session.query(RaspberryJamWorkshop).all()
    user_workshops = []
    for workshop in workshops:
        if login_user in workshop.users:
            user_workshops.append(workshop)
    return user_workshops


def reset_login_user_ics_uuid(user:LoginUser):
    user.ics_uuid = str(uuid.uuid4())
    db_session.commit()
    return user.ics_uuid


def get_links(shortened_link=None, log=False):
    if shortened_link:
        link: Link = db_session.query(Link).filter(Link.link_short == shortened_link).first()
        if link:
            if not link.link_active:
                return None
            if log:
                new_log = LinkLog(link_id=link.link_id)
                db_session.add(new_log)
                db_session.commit()
            return [link]
        else:
            return None
    else:
        links: List[Link] = db_session.query(Link).all()
        return links


def add_link(link_short, link_full, owner:LoginUser):
    new_link = Link()
    new_link.link_short = link_short.strip().lower().replace(" ", "")
    new_link.link_url = link_full.strip().lower().replace(" ", "")
    new_link.user = owner
    current_link:Link = db_session.query(Link).filter(Link.link_short == new_link.link_short).first()
    if current_link:
        return "danger", "Link already exists with that short text!"
    else:
        db_session.add(new_link)
        db_session.commit()
        return "success", "New link added"


def remove_link(link_id):
    link = db_session.query(Link).filter(Link.link_id == int(link_id)).first()
    if link:
        db_session.delete(link)
        db_session.commit()
        return "success", "Link removed"
    else:
        return "danger", "Link not found"


def update_link_active(link_id, active):
    link = db_session.query(Link).filter(Link.link_id == int(link_id)).first()
    if link:
        link.link_active = active
        db_session.commit()
        return "success", "Link updated"
    else:
        return "danger", "Link not found"