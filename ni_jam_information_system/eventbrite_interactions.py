from eventbrite import Eventbrite
from ni_jam_information_system.secret.config import eventbrite_key

eventbrite = Eventbrite(eventbrite_key)


def eventbrite_test():
    print(eventbrite.get_user())
    a = eventbrite.get_user_events(eventbrite.get_user()["id"])
    print(eventbrite.get_user_owned_events(eventbrite.get_user()["id"]))

def get_eventbrite_event_by_id(id):
    return eventbrite.get_event(id)


def get_eventbrite_events_name_id():
    events = eventbrite.get_user_owned_events(eventbrite.get_user()["id"])
    jam_event_names = []
    for event in events["events"]:
        jam_event_names.append({"name":event["name"]["text"], "id":event["id"]})
    return jam_event_names
