import os
from collections import OrderedDict
from enum import Enum
from typing import List, Tuple, Union, Dict

import requests
from threading import Thread

import models
from secrets.config import zenkit_api_key
import database

import hashlib

#WORKSPACE = "My Workspace"
#FACILITATOR_TABLE = "Facilitator - Dummy"
#YZ_SESSION_TABLE = "Youth Zone - dummy"

WORKSPACE = "Mozilla Festival 2019"
FACILITATOR_TABLE = "Facilitators"
YZ_SESSION_TABLE = "Youth Zone"

SCHEDULE_TABLE = "Schedule"

#PUBLIC_YZ_TABLE_SHORT_ID = "Wzt7JDZ3L"
if "PUBLIC_YZ_TABLE_SHORT_ID" in os.environ:
    PUBLIC_YZ_TABLE_SHORT_ID = os.environ["PUBLIC_YZ_TABLE_SHORT_ID"]
else:
    PUBLIC_YZ_TABLE_SHORT_ID = "Wzt7JDZ3L"

PUBLIC_SCHEDULE_TABLE_SHORT_ID = "2RH604FcHf"


class RoomType(Enum):
    NO_REQUIREMENT = 0
    WEB_BROWSER = 1
    LAPTOP = 2
    RASPBERRY_PI = 3
    NO_DATA = 4


class Colours(Enum):
    RED = "#e74c3c"
    WHITE = "#ffffff"
    ORANGE = "#e8cd6d"


class ZenKitBase():
    raw_json = None

    def __init__(self, id, shortId, uuid):
        self.id = id
        self.shortId = shortId
        self.uuid = uuid

    def build_object_from_json(self, json_data):
        self.id = json_data["id"]
        self.shortId = json_data["shortId"]
        self.uuid = json_data["uuid"]

    def add_ids(self, id, shortId, uuid):
        self.id = id
        self.shortId = shortId
        self.uuid = uuid


class CollectionRowFacilitator(ZenKitBase):
    def __init__(self, id, shortId, uuid, first_name, last_name, email_address):
        super().__init__(id, shortId, uuid)
        self.first_name = first_name
        self.last_name = last_name
        self.email_address = email_address
        self.sessions: List[CollectionRowYZ] = []

    @classmethod
    def build_object_from_json(cls, json_data, header_data):
        cls.raw_json = json_data
        id = json_data["id"]
        shortId = json_data["shortId"]
        uuid = json_data["uuid"]
        first_name = match_header_data_to_data(header_data, "first name", json_data)
        last_name = match_header_data_to_data(header_data, "last name", json_data)
        email_address = match_header_data_to_data(header_data, "email address", json_data)
        return cls(id, shortId, uuid, first_name, last_name, email_address)

    @property
    def unique_sessions(self):
        return set(self.sessions)


class CollectionRowYZ(ZenKitBase):
    primary_facilitator: CollectionRowFacilitator = None

    def __init__(self, id, shortId, uuid, title, description, goals, format, post_mozfest, time_required, multiple_numbers, youth_led, materials, primary_facilitator_id=None):
        super().__init__(id, shortId, uuid)
        self.title = title
        self.description = description
        self.goals = goals
        self.format = format
        self.post_mozfest = post_mozfest
        self.time_required = time_required
        self.multiple_numbers = multiple_numbers
        self.youth_led = youth_led
        self.materials = materials
        self.primary_facilitator_id = primary_facilitator_id
        self.room_str = None
        self.room: Room = None
        self.time_slot_str = None
        self.time_slot: TimeSlot = None
        self.header_data = None
        self.status = None
        self.co_facilitator_1_id = None
        self.co_facilitator_2_id = None
        self.co_facilitator_3_id = None
        self.co_facilitator_1: CollectionRowFacilitator = None
        self.co_facilitator_2: CollectionRowFacilitator = None
        self.co_facilitator_3: CollectionRowFacilitator = None
        self.accepted = False
        self.uk_youth = None
        self.youth_reviews: List[models.YouthBlindReview] = []
        self.computer_type = RoomType.NO_DATA
        self.schedule_type = None
        self.old_shortid = None

    @classmethod
    def build_object_from_json(cls, json_data, header_data):
        id = json_data["id"]
        shortId = json_data["shortId"]
        uuid = json_data["uuid"]
        title = match_header_data_to_data(header_data, "title", json_data)
        description = match_header_data_to_data(header_data, "description", json_data)
        goals = match_header_data_to_data(header_data, "goals", json_data)
        format = match_header_data_to_data(header_data, "format", json_data)
        post_mozfest = match_header_data_to_data(header_data, "post-mozfest engagement", json_data)
        time_required = match_header_data_to_data(header_data, "time required", json_data)
        multiple_numbers = match_header_data_to_data(header_data, "dealing with multiple participant numbers", json_data)
        youth_led = match_header_data_to_data(header_data, "youth led", json_data)
        materials = match_header_data_to_data(header_data, "additional materials", json_data)
        primary_facilitator_id = match_header_data_to_data(header_data, "primary facilitator", json_data)
        to_return = cls(id, shortId, uuid, title, description, goals, format, post_mozfest, time_required, multiple_numbers, youth_led, materials, primary_facilitator_id)
        to_return.raw_json = json_data
        to_return.header_data = header_data
        if match_header_data_to_data(header_data, "location", json_data):
            to_return.room_str = match_header_data_to_data(header_data, "location", json_data)[0]
        if match_header_data_to_data(header_data, "time slot", json_data):
            to_return.time_slot_str = match_header_data_to_data(header_data, "time slot", json_data)[0]
        to_return.status = match_header_data_to_data(header_data, "status", json_data)
        to_return.co_facilitator_1_id = match_header_data_to_data(header_data, "co-facilitator #1", json_data)
        to_return.co_facilitator_2_id = match_header_data_to_data(header_data, "co-facilitator #2", json_data)
        to_return.co_facilitator_3_id = match_header_data_to_data(header_data, "co-facilitator #3", json_data)
        to_return.uk_youth = match_header_data_to_data(header_data, "UK Youth", json_data)
        to_return.accepted = match_header_data_to_data(header_data, "Send out accepted email", json_data)
        if match_header_data_to_data(header_data, "Type", json_data):
            to_return.schedule_type = match_header_data_to_data(header_data, "Type", json_data)[0]
        if match_header_data_to_data(header_data, "Facilitator #1", json_data):
            to_return.primary_facilitator_id = match_header_data_to_data(header_data, "Facilitator #1", json_data)
        if match_header_data_to_data(header_data, "Facilitator #2", json_data):
            to_return.co_facilitator_1_id = match_header_data_to_data(header_data, "Facilitator #2", json_data)
        if match_header_data_to_data(header_data, "Facilitator #3", json_data):
            to_return.co_facilitator_2_id = match_header_data_to_data(header_data, "Facilitator #3", json_data)
        if match_header_data_to_data(header_data, "Facilitator #4", json_data):
            to_return.co_facilitator_3_id = match_header_data_to_data(header_data, "Facilitator #4", json_data)
        to_return.old_shortid = match_header_data_to_data(header_data, "Zen ID", json_data)

        return to_return

    def calc_schedule_errors(self):
        error_messages = []
        warning_messages = []

        # Check incorrect day
        if (self.time_slot.day == "Saturday" and not self.can_run_saturday) or (self.time_slot.day == "Sunday" and not self.can_run_sunday):
            error_messages.append(f"This session is unable to run on this day! It must not run on a {self.time_slot.day}!")

        # Check facilitators not double booked
        for session in self.time_slot.sessions.values():
            for facilitator in session.facilitators().keys():
                for s_facilitator in self.facilitators().keys():
                    if facilitator == s_facilitator and session != self:
                        error_messages.append(f"Overlapping facilitators! The facilitator {self.facilitators()[s_facilitator].first_name} {self.facilitators()[s_facilitator].last_name} is also in {session.title}")

        # Check if there is even an admin form submitted for this session
        if not self.data_forms:
            warning_messages.append("No admin form submitted for this session")

        # Check special equipment (microbits for example)

        # Check in valid rooms
        if self.computer_type not in self.room.room_type and self.computer_type != RoomType.NO_REQUIREMENT:
            pass
            error_messages.append(f"Invalid room! This session requires {self.computer_type}")

        if error_messages:
            bg_colour = Colours.RED.value
        elif warning_messages:
            bg_colour = Colours.ORANGE.value
        else:
            bg_colour = Colours.WHITE.value
            error_messages = ["No scheduling errors found", ]

        return bg_colour, error_messages + warning_messages

    @property
    def format_string(self):
        to_return = ""
        for value in self.format:
            to_return = f" {to_return} {value},"
            continue
        return to_return[:-1]

    @property
    def youth_reviews_dict_by_reviewer_id(self):
        to_return = {}
        for review in self.youth_reviews:
            to_return[review.reviewer_id] = review
        return to_return

    @property
    def average_review_score(self):
        total_score = 0
        for review in self.youth_reviews:
            total_score = total_score + review.total_score
        if not total_score:
            return 0
        return round(total_score / len(self.youth_reviews), 1)

    @property
    def is_session_accepted(self):
        if "Accepted" in self.status:
            return True
        return False

    @property
    def can_run_saturday(self):
        for form in self.data_forms:
            if form.day == "Only Sunday":
                return False
        return True

    @property
    def can_run_sunday(self):
        for form in self.data_forms:
            if form.day == "Only Saturday":
                return False
        return True

    @property
    def edit_details_key(self):
        return hashlib.sha256(f"{self.shortId}{session_edit_key}".encode('utf-8')).hexdigest()

    # @property
    def facilitators(self) -> Dict[str, CollectionRowFacilitator]:
        facilitators = {}
        if self.primary_facilitator:
            facilitators[f"{self.primary_facilitator.first_name}-{self.primary_facilitator.email_address}"] = self.primary_facilitator
        if self.co_facilitator_1:
            facilitators[f"{self.co_facilitator_1.first_name}-{self.co_facilitator_1.email_address}"] = self.co_facilitator_1
        if self.co_facilitator_2:
            facilitators[f"{self.co_facilitator_2.first_name}-{self.co_facilitator_2.email_address}"] = self.co_facilitator_2
        if self.co_facilitator_3:
            facilitators[f"{self.co_facilitator_3.first_name}-{self.co_facilitator_3.email_address}"] = self.co_facilitator_3
        return facilitators


class Collection(ZenKitBase):

    def __init__(self, id, shortId, uuid, name):
        super().__init__(id, shortId, uuid)
        self.name = name
        self.entities: Union[List[CollectionRowYZ], List[CollectionRowFacilitator]] = []
        self.rooms: Dict[str, Room] = {}
        self.time_slots: Dict[str, TimeSlot] = {}

    @classmethod
    def build_object_from_json(cls, json_data):
        return cls(json_data["id"], json_data["shortId"], json_data["uuid"], json_data["name"])

    @property
    def rooms_sorted(self):
        sorted_rooms = OrderedDict()
        for key in sorted(self.rooms.keys()):
            sorted_rooms[key] = self.rooms[key]
        return sorted_rooms

    @property
    def time_slots_sorted(self):
        sorted_time_slots = OrderedDict()
        for key in sorted(self.time_slots.keys()):
            sorted_time_slots[key] = self.time_slots[key]
        return sorted_time_slots

    @property
    def time_slots_sorted_saturday(self):
        sat_slots = OrderedDict()
        for slot in self.time_slots_sorted.keys():
            if "Sat" in slot:
                sat_slots[slot] = self.time_slots_sorted[slot]
        return sat_slots

    @property
    def time_slots_sorted_sunday(self):
        sun_slots = OrderedDict()
        for slot in self.time_slots_sorted.keys():
            if "Sun" in slot:
                sun_slots[slot] = self.time_slots_sorted[slot]
        return sun_slots


class CollectionYZ(Collection):
    def __init__(self, id, shortId, uuid, name):
        super().__init__(id, shortId, uuid, name)
        self.entities: List[CollectionRowYZ] = []

    def get_lowest_review_sessions(self, reviewer_id) -> List[CollectionRowYZ]:
        lowest_review_sessions = []
        reviews = 100
        for session in self.entities:
            if len(session.youth_reviews) < reviews and reviewer_id not in session.youth_reviews_dict_by_reviewer_id.keys():
                reviews = len(session.youth_reviews)
                lowest_review_sessions = [session, ]
            elif len(session.youth_reviews) == reviews and reviewer_id not in session.youth_reviews_dict_by_reviewer_id.keys():
                lowest_review_sessions.append(session)
        if reviews == 100:
            return None
        return lowest_review_sessions

    @property
    def entities_dict(self) -> Dict[str, CollectionRowYZ]:
        to_return_entities_dict = {}
        for entity in self.entities:
            to_return_entities_dict[entity.shortId] = entity

        return to_return_entities_dict

    @property
    def entities_dict_edit_key(self) -> Dict[str, CollectionRowYZ]:
        to_return_entities_dict = {}
        for entity in self.entities:
            to_return_entities_dict[entity.edit_details_key] = entity

        return to_return_entities_dict

    @property
    def entities_accepted(self) -> List[CollectionRowYZ]:
        accepted = []
        for entity in self.entities:
            if entity.is_session_accepted:
                accepted.append(entity)
        return accepted


class Workspace(ZenKitBase):
    def __init__(self, id, shortId, uuid, name):
        super().__init__(id, shortId, uuid)
        self.name = name
        self.collections: List[Collection] = []

    @classmethod
    def build_object_from_json(cls, json_data):
        workspace = cls(json_data["id"], json_data["shortId"], json_data["uuid"], json_data["name"])
        for collection_json in json_data["lists"]:
            if "youth zone" in collection_json["name"].lower():
                workspace.collections.append(CollectionYZ.build_object_from_json(collection_json))
            else:
                workspace.collections.append(Collection.build_object_from_json(collection_json))
        return workspace


class Room():
    def __init__(self, room_name, time_slots):
        self.sessions: Dict[TimeSlot, CollectionRowYZ] = {}
        self.room_name = room_name
        self.time_slots: Dict[str, TimeSlot] = time_slots
        self.room_type: List[RoomType] = []

        if "211" in self.room_name:
            self.room_type.append(RoomType.WEB_BROWSER)
        elif "210" in self.room_name:
            self.room_type.append(RoomType.RASPBERRY_PI)
            self.room_type.append(RoomType.WEB_BROWSER)
        elif "207" in self.room_name:
            self.room_type.append(RoomType.LAPTOP)
            self.room_type.append(RoomType.WEB_BROWSER)

        else:
            self.room_type.append(RoomType.NO_REQUIREMENT)

    @property
    def schedule_room(self):
        schedule_time_slots = OrderedDict()
        for time_slot in sorted(self.time_slots.keys()):
            schedule_time_slots[time_slot] = None
        for session in list(self.sessions.values()):
            if session.time_slot:
                schedule_time_slots[session.time_slot.day_time] = session
        return schedule_time_slots


class TimeSlot():
    def __init__(self, raw_day_time, rooms):
        self.sessions: Dict[Room, CollectionRowYZ] = {}
        self.day_time = raw_day_time
        self.rooms: Dict[str, Room] = rooms
        if "Sat" in self.day_time:
            self.day = "Saturday"
        elif "Sun" in self.day_time:
            self.day = "Sunday"
        else:
            self.day = None

    @property
    def schedule_time_slot(self):
        schedule_rooms = OrderedDict()
        for room in sorted(self.rooms.keys()):
            schedule_rooms[room] = None
        for session in list(self.sessions.values()):
            if session.room:
                schedule_rooms[session.room.room_name] = session
        return schedule_rooms


def make_zenkit_request_get(endpoint: str, parameter: str = ""):
    if parameter:
        parameter = f"/{parameter}"
    url = f"https://zenkit.com{endpoint}{parameter}"
    headers = {'Zenkit-API-Key': zenkit_api_key}
    data = requests.get(url, headers=headers).json()
    return data


def make_zenkit_request_post(endpoint: str, parameter: str = "", payload=()):
    if parameter:
        parameter = f"/{parameter}"
    url = f"https://zenkit.com{endpoint}{parameter}"
    headers = {'Zenkit-API-Key': zenkit_api_key}
    data = requests.post(url, headers=headers, data=payload).json()
    return data



def get_specific_collection_by_shortid(collection_shortid):
    collection = CollectionYZ("1", collection_shortid, "", "Youth Zone")
    return collection


def match_header_data_to_data(header_data, row_title, row_data):
    for row_header in header_data:
        if row_header["name"].lower() == row_title.lower():
            found_row_header = row_header
            break
    else:
        return None

    # Check if it is a labels list, if so, get the names of the labels
    if "categories" in found_row_header["businessData"]:
        column_name_uuid = f'{found_row_header["uuid"]}_categories_sort'
        for column_key in row_data:
            if str(column_key).startswith(column_name_uuid):
                to_return = []
                for category in row_data[column_name_uuid]:
                    to_return.append(category["name"])
                return to_return
        else:
            return None
    else:

        for column_key in row_data:
            if str(column_key).startswith(found_row_header["uuid"]):
                return row_data[column_key]
        else:
            return None


def build_workspaces():
    workspaces: List[Workspace] = []
    json_data = make_zenkit_request_get("/api/v1/users/me/workspacesWithLists")
    for workspace_json in json_data:
        workspaces.append(Workspace.build_object_from_json(workspace_json))
    return workspaces

def get_specific_collection_by_name(workspace_name, collection_name):
    workspaces = build_workspaces()
    for potential_workspace in workspaces:
        if potential_workspace.name == workspace_name:
            workspace = potential_workspace
            break
    else:
        return None
    for potential_collection in workspace.collections:
        if potential_collection.name == collection_name:
            collection = potential_collection
            break
    else:
        return None
    return collection


def get_collection_column_header_data(listShortId):
    data = make_zenkit_request_get(f"/api/v1/lists/{listShortId}/elements")
    return data


def build_yz_table(collection_yz=None, collection_shortid=None) -> CollectionYZ:
    if collection_shortid:
        collection = get_specific_collection_by_shortid(collection_shortid)
    else:
        collection = get_specific_collection_by_name(WORKSPACE, YZ_SESSION_TABLE)
    entries = make_zenkit_request_post(f"/api/v1/lists/{collection.shortId}/entries/filter/list", payload={"limit":500})
    header_data = get_collection_column_header_data(collection.shortId)
    for row in entries["listEntries"]:
        collection.entities.append(CollectionRowYZ.build_object_from_json(row, header_data))
    collection_yz.append(collection)
    return collection

#  -> List[models.Workshop]
def link_workshops_to_yz_sessions(collection_yz: CollectionYZ):
    workshops = database.get_workshops_to_select().all()
    sessions_dict: Dict[str, CollectionRowYZ] = {}
    for session in collection_yz.entities:
        if session.schedule_type == "Youth Zone":
            sessions_dict[session.old_shortid] = session
    print(f"Length is {len(sessions_dict)}")
    #for session in sessions_dict.keys():
        #print(session)
    for workshop in workshops:
        if workshop.workshop_shortid in sessions_dict:
            workshop.session = sessions_dict[workshop.workshop_shortid]
        else:
            print(f"Unable to find {workshop.workshop_title} in Zenkit import!")
    return workshops


def build_room_time_slots(yz_collection: CollectionYZ):
    for session in yz_collection.entities_accepted:
        if session.room_str:
            if not session.room_str in yz_collection.rooms.keys():
                yz_collection.rooms[session.room_str] = Room(session.room_str, time_slots=yz_collection.time_slots)
            session.room = yz_collection.rooms[session.room_str]
            yz_collection.rooms[session.room_str].sessions[session.shortId] = session

        if session.time_slot_str:
            if not session.time_slot_str in yz_collection.time_slots.keys():
                yz_collection.time_slots[session.time_slot_str] = TimeSlot(session.time_slot_str, rooms=yz_collection.rooms)
            session.time_slot = yz_collection.time_slots[session.time_slot_str]
            yz_collection.time_slots[session.time_slot_str].sessions[session.shortId] = session
    return yz_collection