from eventbrite import Eventbrite

import configuration
from secrets.config import eventbrite_key

class MyEventbrite(Eventbrite):
    # From https://github.com/eventbrite/eventbrite-sdk-python/issues/18
    # For getting all attendees
    def get_event_attendees(self, event_id, status=None,
                            changed_since=None, page=1):
        """
        Returns a paginated response with a key of attendees, containing a
        list of attendee.

        GET /events/:id/attendees/
        """
        data = {}
        if status:  # TODO - check the types of valid status
            data['status'] = status
        if changed_since:
            data['changed_since'] = changed_since
        data['page'] = page
        return self.get("/events/{0}/attendees/".format(event_id), data=data)

    def get_all_event_attendees(self, event_id, status=None,
                                changed_since=None):
        """
        Returns a full list of attendees.

        TODO: figure out how to use the 'continuation' field properly
        """
        page = 1
        attendees = []
        while True:
            r = self.get_event_attendees(event_id, status,
                                         changed_since, page=page)
            attendees.extend(r['attendees'])
            if r['pagination']['page_count'] <= page:
                break
            page += 1
        return {"attendees": attendees}



eventbrite = MyEventbrite(eventbrite_key)


def eventbrite_test():
    print(eventbrite.get_user())
    a = eventbrite.get_user_events(eventbrite.get_user()["id"])
    print(eventbrite.get_user_owned_events(eventbrite.get_user()["id"]))

def get_eventbrite_event_by_id(id):
    return eventbrite.get_event(id)


def get_eventbrite_events_name_id():
    if not eventbrite_key:
        return []
    eventbrite_user = eventbrite.get_user()
    organisations = eventbrite.get("/users/me/organizations/")["organizations"]
    if organisations:
        if len(organisations) > 1:
            for organisation in organisations:
                if organisation["name"] == configuration.verify_config_item("general", "jam_organisation_name"):
                    eventbrite_organisation = organisation
                    break
            else:
                return {}
        else:
            eventbrite_organisation = organisations[0]
    else:
        return {}


    events = eventbrite.get(f"/organizations/{eventbrite_organisation['id']}/events/", data={"page_size":200})
    jam_event_names = []
    for event in events["events"]:
        jam_event_names.append({"name":event["name"]["text"], "id":event["id"]})
    return jam_event_names


def get_eventbrite_attendees_for_event(event_id):
    return eventbrite.get_all_event_attendees(event_id)