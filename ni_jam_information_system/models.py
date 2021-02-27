import datetime
import enum
from typing import List
import enum
import database
import math

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, BigInteger, Time, Boolean, text, Enum
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from secrets.config import db_user, db_pass, db_name, db_host
from sqlalchemy.ext.hybrid import hybrid_property


engine = create_engine('mysql+pymysql://{}:{}@{}/{}?charset=utf8'.format(db_user, db_pass, db_host, db_name))
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()
metadata = Base.metadata


class EventSourceEnum(enum.Enum):
    eventbrite = 1
    standalone = 2


class CertificateTypeEnum(enum.Enum):
    DBS_Update_Service = 1
    DBS_No_Update_Service = 2
    Access_NI = 3
    PVG = 4
    Garda = 5
    Other = 6

    @classmethod
    def dropdown_view(cls):
        to_return = []
        for item in CertificateTypeEnum:
            to_return.append([item.value, item.name])
        return to_return


class FileTypeEnum(enum.Enum):
    Teacher_Guide = 1
    Worksheet = 2
    Code = 3
    Other = 4

    @classmethod
    def dropdown_view(cls):
        to_return = []
        for item in FileTypeEnum:
            to_return.append([item.value, item.name])
        return to_return


class Attendee(Base):
    __tablename__ = 'attendees'

    attendee_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    first_name = Column(String(45), nullable=False)
    surname = Column(String(45), nullable=False)
    age = Column(Integer)
    email_address = Column(String(45), nullable=False)
    gender = Column(String(45))
    town = Column(String(45))
    experience_level = Column(String(45))
    school = Column(String(45))
    order_id = Column(BigInteger)
    ticket_type = Column(String(45))
    jam_id = Column(ForeignKey('raspberry_jam.jam_id'), primary_key=True, nullable=False, index=True)
    checked_in = Column(Integer)
    current_location = Column(String(15))
    attendee_login_id = Column(ForeignKey('attendee_login.attendee_login_id'), primary_key=False, nullable=True, index=True, unique=True)
    attendee_login = relationship('AttendeeLogin')

    jam = relationship('RaspberryJam')


class Configuration(Base):
    __tablename__ = 'configuration'

    config_id = Column(Integer, primary_key=True, unique=True)
    config_name = Column(String(45))
    config_value = Column(String(45))


class Group(Base):
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True, unique=True)
    group_name = Column(String(45))


class JamAttendance(Base):
    __tablename__ = 'jam_attendance'

    attendee_id = Column(Integer, primary_key=True, nullable=False)
    jam_id = Column(BigInteger, primary_key=True, nullable=False)
    checked_in = Column(Integer)


class LoginCookie(Base):
    __tablename__ = 'login_cookie'

    cookie_id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    cookie_value = Column(String(45))
    cookie_expiry = Column(DateTime)
    user_id = Column(ForeignKey('login_users.user_id'), primary_key=True, nullable=False, index=True)

    user = relationship("LoginUser")


class LoginUser(Base):
    __tablename__ = 'login_users'

    user_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    username = Column(String(45), nullable=False, unique=True)
    password_hash = Column(String(100), nullable=False)
    password_salt = Column(String(45), nullable=False)
    first_name = Column(String(45), nullable=False)
    surname = Column(String(45), nullable=False)
    volunteer = Column(Integer)
    group_id = Column(ForeignKey('groups.group_id'), primary_key=True, nullable=False, index=True)
    email = Column(String(45))
    reset_code = Column(String(10))
    active = Column(Integer)
    forgotten_password_url = Column(String(100), nullable=True, unique=True)
    forgotten_password_expiry = Column(DateTime, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    ics_uuid = Column(String(36), unique=True)

    attending = relationship("VolunteerAttendance")
    group = relationship('Group')
    login_cookie = relationship('LoginCookie')
    workshop_runs = relationship('RaspberryJamWorkshop', secondary='workshop_volunteers')
    police_checks = relationship("PoliceCheck", foreign_keys="[PoliceCheck.user_id]", uselist=True)
    attend = None

    @hybrid_property
    def date_of_birth_str(self):
        if self.date_of_birth:
            return self.date_of_birth.strftime("%d-%m-%Y")
        return None

    @hybrid_property
    def most_recent_dbs_update_cert_or_other(self):
        most_recent_dbs = None
        most_recent_other = None

        # TODO : Section below needs completed
        for cert in self.police_checks:
            if cert.update_service:
                if not most_recent_dbs:
                    most_recent_dbs = cert
                    continue
                else:
                    if most_recent_dbs.time_delta_till_expiry.days < cert.time_delta_till_expiry.days:
                        most_recent_dbs = cert
            else:
                if cert.update_service:
                    if not most_recent_other:
                        most_recent_other = cert
                        continue
                    else:
                        if most_recent_other.time_delta_till_expiry.days < cert.time_delta_till_expiry.days:
                            most_recent_other = cert

        if self.police_checks:
            return self.police_checks[:0]

    @hybrid_property
    def police_cert_status(self):
        if self.date_of_birth:
            days_since_dob = (datetime.datetime.now() - self.date_of_birth).days
            if days_since_dob < 6205:  # Number of days in 17 years
                return f"Not required, {math.floor(days_since_dob / 365)} years old", database.light_grey
            for cert in self.police_checks:
                if cert.is_valid:
                    return cert._status
        else:
            return "No DoB", database.lighter_blue
        return "No certificate", database.orange
    
    @hybrid_property
    def police_check_required_message(self):
        if self.date_of_birth:
            days_since_dob = (datetime.datetime.now() - self.date_of_birth).days
            if days_since_dob > 6205:  # Number of days in 17 years
                return f"<b>Yes</b> as you are {math.floor(days_since_dob / 365)} years old. A police check is required at age 17 and above."
            else:
                return f"<b>No</b> as you are only {math.floor(days_since_dob / 365)} years old. A police check is only required at age 17 and above."
        else:
            return "<b>Unknown</b> - No DoB in the system..."

    @hybrid_property
    def workshop_runs_current_jam(self) -> List['RaspberryJamWorkshop']:
        workshop_runs_return = []
        jam_id = database.get_current_jam_id()
        for workshop_return in self.workshop_runs:
            if workshop_return.jam_id == jam_id:
                workshop_runs_return.append(workshop_return)
        return workshop_runs_return


class PagePermission(Base):
    __tablename__ = 'page_permissions'

    page_id = Column(Integer, primary_key=True, nullable=False)
    page_name = Column(String(45), nullable=False)
    group_required = Column(ForeignKey('groups.group_id'), primary_key=True, nullable=False, index=True)

    group = relationship('Group')


class RaspberryJam(Base):
    __tablename__ = 'raspberry_jam'

    jam_id = Column(BigInteger, primary_key=True)
    name = Column(String(150), nullable=False)
    date = Column(DateTime, nullable=False)
    food_after = Column(Integer)
    jam_password = Column(String(45), nullable=True)
    event_source = Column(Enum(EventSourceEnum))
    volunteer_attendance = relationship('VolunteerAttendance')
    attendees = relationship('Attendee')

    @hybrid_property
    def volunteers_attending_jam(self):
        attending = []
        for volunteer_attendance in self.volunteer_attendance:
            if volunteer_attendance.volunteer_attending or volunteer_attendance.setup_attending:
                attending.append(volunteer_attendance.user)
        return attending

    @hybrid_property
    def volunteer_replied_attendance(self):
        replied = []
        for volunteer_attendance in self.volunteer_attendance:
            replied.append(volunteer_attendance.user)
        return replied


class RaspberryJamWorkshop(Base):
    __tablename__ = 'raspberry_jam_workshop'

    workshop_run_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    jam_id = Column(ForeignKey('raspberry_jam.jam_id'), primary_key=True, nullable=False, index=True)
    workshop_id = Column(ForeignKey('workshop.workshop_id'), primary_key=True, nullable=False, index=True)
    workshop_room_id = Column(ForeignKey('workshop_room.room_id'), primary_key=True, nullable=False, index=True)
    workshop_time_slot = Column(String(45))
    slot_id = Column(ForeignKey('workshop_slots.slot_id'), primary_key=True, nullable=False, index=True)
    pilot = Column(Integer, nullable=False, server_default=text("'0'"))
    pair = Column(Integer, nullable=False, server_default=text("'0'"))

    jam = relationship('RaspberryJam')
    slot = relationship('WorkshopSlot')
    workshop = relationship('Workshop')
    workshop_room = relationship('WorkshopRoom')
    users = relationship('LoginUser', secondary='workshop_volunteers')
    attendees = relationship('Attendee', secondary='workshop_attendee')

    @hybrid_property
    def max_attendees(self):
        if int(self.workshop_room.room_capacity) < int(self.workshop.workshop_limit):
            return int(self.workshop_room.room_capacity)
        else:
            return int(self.workshop.workshop_limit)

    @hybrid_property
    def leading_volunteer(self):
        if self.users:
            return f"{self.users[0].first_name} {self.users[0].surname}"
        return ""

    @hybrid_property
    def attendee_first_names(self):
        to_return = ""
        for attendee in self.attendees:
            to_return = f"{to_return} {attendee.first_name},"
        if to_return:
            return to_return[:-1]
        return to_return


class VolunteerAttendance(Base):
    __tablename__ = 'volunteer_attendance'

    user_id = Column(ForeignKey('login_users.user_id'), primary_key=True, nullable=False, index=True)
    jam_id = Column(ForeignKey('raspberry_jam.jam_id'), primary_key=True, nullable=False, index=True)
    volunteer_attending = Column(Integer)
    setup_attending = Column(Integer)
    packdown_attending = Column(Integer)
    food_attending = Column(Integer)
    notes = Column(String(300))
    current_location = Column(String(15))
    last_edit_date = Column(DateTime, default=datetime.datetime.utcnow)
    arrival_time = Column(Time)

    jam = relationship('RaspberryJam')
    user = relationship('LoginUser')


class Workshop(Base):
    __tablename__ = 'workshop'

    workshop_id = Column(Integer, primary_key=True)
    workshop_title = Column(String(45), nullable=False)
    workshop_limit = Column(Integer, nullable=False)
    workshop_description = Column(String(500))
    workshop_level = Column(String(45))
    workshop_hidden = Column(Integer, nullable=False)
    workshop_url = Column(String(300))
    workshop_volunteer_requirements = Column(Integer)
    workshop_archived = Column(Integer)

    workshop_files: List["WorkshopFile"] = relationship('WorkshopFile')
    #workshop_equipment = relationship("Equipment", secondary="workshop_equipment")
    workshop_equipment = relationship('WorkshopEquipment')
    badges = relationship('BadgeLibrary', secondary='workshop_badge')
    workshop_badge = relationship('BadgeLibrary', uselist=False)
    
    @hybrid_property
    def workshop_name_file_status(self):
        teacher = ""
        worksheet = ""
        for file in self.workshop_files:
            if file.file_type == FileTypeEnum.Teacher_Guide:
                teacher = " 🍎"
            elif file.file_type == FileTypeEnum.Worksheet:
                worksheet = " 📝️"
        return f"{self.workshop_title}{worksheet}{teacher}"


class WorkshopAttendee(Base):
    __tablename__ = 'workshop_attendee'

    attendee_id = Column(ForeignKey('attendees.attendee_id'), primary_key=True, nullable=False, index=True)
    workshop_run_id = Column(ForeignKey('raspberry_jam_workshop.workshop_run_id'), primary_key=True, nullable=False, index=True)
    attended = Column(Integer)

    attendee = relationship('Attendee')
    workshop_run = relationship('RaspberryJamWorkshop')


class WorkshopRoom(Base):
    __tablename__ = 'workshop_room'

    room_id = Column(Integer, primary_key=True, unique=True)
    room_name = Column(String(45))
    room_capacity = Column(String(45))
    room_volunteers_needed = Column(Integer, nullable=False)


class WorkshopSlot(Base):
    __tablename__ = 'workshop_slots'

    slot_id = Column(Integer, primary_key=True)
    slot_time_start = Column(Time, nullable=False)
    slot_time_end = Column(Time, nullable=False)
    slot_hidden = Column(Boolean, nullable=False)
    workshops_in_slot: List[RaspberryJamWorkshop] = relationship("RaspberryJamWorkshop")

    @property
    def title(self):
        return f"{self.slot_time_start} - {self.slot_time_end}"

    @property
    def volunteers_busy_in_slot(self):
        jam_id = database.get_current_jam_id()
        volunteers: List[LoginUser] = []
        for workshop in self.workshops_in_slot:
            if workshop.jam_id == jam_id:
                volunteers = [*volunteers, *workshop.users] # Merge lists together
        return volunteers


class WorkshopFile(Base):
    __tablename__ = 'workshop_files'

    file_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    file_title = Column(String(90), nullable=False)
    file_path = Column(String(150), nullable=False)
    file_permission = Column(String(45), nullable=False)
    file_edit_date = Column(DateTime, nullable=False)
    file_type = Column(Enum(FileTypeEnum), nullable=False)
    workshop_id = Column(ForeignKey('workshop.workshop_id'), primary_key=True, nullable=False, index=True)


class WorkshopEquipment(Base):
    __tablename__ = 'workshop_equipment'

    equipment_id = Column(ForeignKey('equipment.equipment_id'), primary_key=True, nullable=False, index=True)
    workshop_id = Column(ForeignKey('workshop.workshop_id'), primary_key=True, nullable=False, index=True)
    equipment_per_attendee = Column(Boolean)
    equipment_quantity = Column(Integer)

    equipment = relationship("Equipment")
    workshop = relationship("Workshop")


class Equipment(Base):
    __tablename__ = 'equipment'

    equipment_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    equipment_name = Column(String(150), nullable=False)
    equipment_code = Column(String(6), nullable=False)
    equipment_group_id = Column(ForeignKey('equipment_group.equipment_group_id'), primary_key=True, nullable=False, index=True)
    equipment_group = relationship("EquipmentGroup")
    equipment_entries = relationship("EquipmentEntry")


class EquipmentGroup(Base):
    __tablename__ = 'equipment_group'
    equipment_group_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    equipment_group_name = Column(String(45), nullable=False)


class EquipmentEntry(Base):
    __tablename__ = 'equipment_entry'
    equipment_entry_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    equipment_id = Column(ForeignKey('equipment.equipment_id'), primary_key=True, nullable=False, index=True)
    equipment_entry_number = Column(Integer, nullable=False)
    equipment_inventories = relationship("InventoryEquipmentEntry")
    attached_equipment = relationship("Equipment")


class InventoryEquipmentEntry(Base):
    __tablename__ = 'inventory_equipment_entry'
    inventory_id = Column(ForeignKey('inventory.inventory_id'), primary_key=True, nullable=False, index=True)
    equipment_entry_id = Column(ForeignKey('equipment_entry.equipment_entry_id'), primary_key=True, nullable=False, index=True)
    entry_quantity = Column(Integer, nullable=False)

    inventory = relationship("Inventory")
    equipment_entry = relationship("EquipmentEntry")


class Inventory(Base):
    __tablename__ = 'inventory'
    inventory_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    inventory_title = Column(String(45), nullable=False)
    inventory_date = Column(DateTime(), nullable=False)


class AttendeeLogin(Base):
    __tablename__ = 'attendee_login'
    attendee_login_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    attendee_login_name = Column(String(45), nullable=False, unique=True)
    attendee_badges = relationship("BadgeLibrary", secondary='attendee_login_badges')
    attendee_references = relationship("Attendee")


class AttendeeLoginBadges(Base):
    __tablename__ = 'attendee_login_badges'
    attendee_login_id = Column(ForeignKey('attendee_login.attendee_login_id'), primary_key=True, nullable=False, index=True)
    badge_id = Column(ForeignKey('badge_library.badge_id'), primary_key=True, nullable=False, index=True)
    badge_award_date = Column(DateTime, nullable=False)


class BadgeDependencies(Base):
    __tablename__ = 'badge_dependencies'
    badge_dependency_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    parent_badge_id = Column(ForeignKey('badge_library.badge_id'), primary_key=True, nullable=False, index=True)
    dependency_badge_id = Column(ForeignKey('badge_library.badge_id'), primary_key=True, nullable=False, index=True)
    badge_awarded_core = Column(Boolean, nullable=False)
    badge = relationship("BadgeLibrary", foreign_keys=parent_badge_id)
    dependency_badge = relationship("BadgeLibrary", foreign_keys=dependency_badge_id)


class BadgeLibrary(Base):
    __tablename__ = 'badge_library'
    badge_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    badge_name = Column(String(55), nullable=False, unique=True)
    badge_description = Column(String(200), nullable=False)
    badge_hidden = Column(Boolean, nullable=False)
    badge_children_required_count = Column(Integer, nullable=False)
    workshop_id = Column(ForeignKey('workshop.workshop_id'), primary_key=False, nullable=True, index=True, unique=True)
    badge_icon_path = Column(String(150), nullable=True)
    badge_dependencies: List[BadgeDependencies] = relationship('BadgeDependencies', foreign_keys=BadgeDependencies.parent_badge_id, uselist=True) 

    @hybrid_property
    def dependent_badges(self):
        badges = []
        for badge_dependency in self.badge_dependencies:
            badges.append(badge_dependency.dependency_badge)
        return badges


class WorkshopBadge(Base):
    __tablename__ = 'workshop_badge'
    badge_id = Column(ForeignKey('badge_library.badge_id'), primary_key=True, nullable=False, index=True)
    workshop_id = Column(ForeignKey('workshop.workshop_id'), primary_key=True, nullable=False, index=True)
    workshop = relationship('Workshop')
    badge = relationship('BadgeLibrary')


class AlertConfig(Base):
    __tablename__ = 'alert_config'
    alert_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    alert_message = Column(String(300), nullable=False)
    jam_id = Column(ForeignKey('raspberry_jam.jam_id'), primary_key=True, nullable=True, index=True)
    workshop_id = Column(ForeignKey('workshop.workshop_id'), primary_key=True, nullable=True, index=True)
    ticket_type = Column(String(45), nullable=True)
    slot_id = Column(ForeignKey('workshop_slots.slot_id'), primary_key=True, nullable=True, index=True)


class PoliceCheck(Base):
    __tablename__ = "police_checks"
    certificate_table_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    user_id = Column(ForeignKey('login_users.user_id'), primary_key=False, nullable=False, index=True)

    certificate_reference = Column(String(45), nullable=True)
    certificate_issue_date = Column(DateTime, nullable=True)
    certificate_type = Column(Enum(CertificateTypeEnum), nullable=False)
    certificate_expiry_date = Column(DateTime, nullable=True)
    certificate_last_digital_checked = Column(DateTime, nullable=True)

    certificate_application_date = Column(DateTime, nullable=False)

    certificate_update_service_safe = Column(Boolean, nullable=False)

    certificate_in_person_verified_on = Column(DateTime, nullable=True)
    verified_in_person_by_user = Column(ForeignKey('login_users.user_id'), primary_key=False, nullable=True, index=True)

    user = relationship("LoginUser", foreign_keys=user_id, uselist=False)
    verified_by_user = relationship("LoginUser", foreign_keys=verified_in_person_by_user, uselist=False)

    @hybrid_property
    def _status(self):
        if self.certificate_issue_date and self.certificate_expiry_date and self.certificate_application_date and self.certificate_type and self.certificate_reference:
            if self.time_delta_till_expiry.days < 0:
                return "Certificate has now expired!", database.red 
            elif self.time_delta_till_expiry.days < 60:
                return f"Expires in {self.time_delta_till_expiry.days} days!", database.orange 
            
            elif self.certificate_type == CertificateTypeEnum.DBS_Update_Service:
                if self.certificate_update_service_safe and self.certificate_in_person_verified_on:
                    return "Valid and verified", database.green
                elif self.certificate_update_service_safe:
                    return "Verified online, awaiting in person verification", database.yellow
                elif not self.user.date_of_birth:
                    return "No DoB in the system", database.red
                elif self.certificate_last_digital_checked:
                    return "Invalid or Warning", database.red
                else:
                    return "Not verified", database.orange
            else:
                if self.certificate_in_person_verified_on:
                    return "Valid and verified", database.green
                else:
                    return "Awaiting in person verification", database.yellow
        else:
            return "Incomplete certificate", "#ffffff"

    @hybrid_property
    def status(self):
        return self._status[0]

    @hybrid_property
    def status_colour(self):
        return self._status[1]

    @hybrid_property
    def update_service(self):
        if self.certificate_type == CertificateTypeEnum.DBS_Update_Service:
            return True
        return False

    @hybrid_property
    def verify_button_status(self):
        if self.certificate_type == CertificateTypeEnum.DBS_Update_Service and self.certificate_expiry_date and self.certificate_issue_date and self.certificate_reference:
            return "", ""
        elif not self.user.date_of_birth:
            return 'disabled', "User has no date of birth on the system"
        else:
            return 'disabled', "Missing either certificate reference, issue date or expiry date"

    @hybrid_property
    def certificate_issue_date_str(self):
        if self.certificate_issue_date:
            return self.certificate_issue_date.strftime("%d-%m-%Y")
        return None

    @hybrid_property
    def certificate_expiry_date_str(self):
        if self.certificate_expiry_date:
            return self.certificate_expiry_date.strftime("%d-%m-%Y")
        return None

    @hybrid_property
    def certificate_last_digital_checked_str(self):
        if self.certificate_last_digital_checked:
            return self.certificate_last_digital_checked.strftime("%d-%m-%Y")
        return None

    @hybrid_property
    def time_delta_till_expiry(self):
        return self.certificate_expiry_date - datetime.datetime.today()

    @hybrid_property
    def is_valid(self):
        if self.certificate_expiry_date and self.time_delta_till_expiry.days > 0:
            return True
        return False


t_workshop_volunteers = Table(
    'workshop_volunteers', metadata,
    Column('user_id', ForeignKey('login_users.user_id'), primary_key=True, nullable=False, index=True),
    Column('workshop_run_id', ForeignKey('raspberry_jam_workshop.workshop_run_id'), primary_key=True, nullable=False, index=True)
)

