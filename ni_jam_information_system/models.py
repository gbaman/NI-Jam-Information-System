from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, BigInteger, Time, Boolean, text
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from secrets.config import db_user, db_pass, db_name, db_host


engine = create_engine('mysql+pymysql://{}:{}@{}/{}?charset=utf8'.format(db_user, db_pass, db_host, db_name))
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()
metadata = Base.metadata

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

    attending = relationship("VolunteerAttendance")
    group = relationship('Group')
    login_cookie = relationship('LoginCookie')
    workshop_runs = relationship('RaspberryJamWorkshop', secondary='workshop_volunteers')


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

    workshop_files = relationship('WorkshopFile')
    #workshop_equipment = relationship("Equipment", secondary="workshop_equipment")
    workshop_equipment = relationship('WorkshopEquipment')


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
    workshops_in_slot = relationship("RaspberryJamWorkshop")


class WorkshopFile(Base):
    __tablename__ = 'workshop_files'

    file_id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    file_title = Column(String(90), nullable=False)
    file_path = Column(String(150), nullable=False)
    file_permission = Column(String(45), nullable=False)
    file_edit_date = Column(DateTime, nullable=False)
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


t_workshop_volunteers = Table(
    'workshop_volunteers', metadata,
    Column('user_id', ForeignKey('login_users.user_id'), primary_key=True, nullable=False, index=True),
    Column('workshop_run_id', ForeignKey('raspberry_jam_workshop.workshop_run_id'), primary_key=True, nullable=False, index=True)
)

