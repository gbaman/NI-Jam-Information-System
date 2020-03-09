from copy import deepcopy


def ldn_jam_generate_ids(attendees):
    # A custom importer adapter for the London Jam
    new_attendees = []
    for attendee in attendees:
        attendees = []
        if attendee["ticket_class_name"] == "Family ticket - option 1":
            attendees = [attendee]
        elif attendee["ticket_class_name"] == "Family ticket - option 2":
            attendees = [attendee, deepcopy(attendee)]
            attendees[1]["id"] = "10" + attendees[1]["id"][2:]
        elif attendee["ticket_class_name"] == "Family ticket - option 3":
            attendees = [attendee, deepcopy(attendee), deepcopy(attendee)]
            attendees[1]["id"] = "10" + attendees[1]["id"][2:]
            attendees[2]["id"] = "11" + attendees[2]["id"][2:]
        new_attendees = new_attendees + attendees
    for attendee in new_attendees:
        attendee["ticket_class_name"] = "First-timer"
    return new_attendees
