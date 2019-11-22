import slack_messages
import database
import models
import configuration
import datetime


def send_jam_sessions_summery(user: models.LoginUser):
    slots_to_notify = configuration.verify_config_item_list("notification", "enable_notifications_for_slot_ids")
    if not slots_to_notify:
        slots_to_notify = list(range(0, 100))
    message="""
*Jam summary*
-----------\n"""
    for workshop in user.workshop_runs_current_jam:
        if workshop.slot.slot_id in slots_to_notify:
            message = f"""{message}*{workshop.slot.title}* -- {workshop.workshop.workshop_title} ::: _{workshop.workshop_room.room_name}_\n"""
    print(message)
    slack_messages.send_slack_direct_message([user], message)


def send_latecomer_workshop_signup_reminder():
    users_to_message = []
    # Remind all volunteers who are going to be late, to fill in NIJIS volunteer signup
    for volunteer in database.get_attending_volunteers(database.get_current_jam_id())[0]:
        if volunteer.attend and volunteer.attend.arrival_time and volunteer.attend.arrival_time > datetime.datetime.strptime('12:00', '%H:%M').time():
            users_to_message.append(volunteer)
    slack_messages.send_slack_direct_message(users_to_message, "A quick reminder, as you are due to arrive *after* the Jam briefing at 11:45am, please make sure you have signed up to the workshops you want to help with before 11:30am on the Saturday of the Jam! \n It should only take 30s. \n https://workshops.niraspberryjam.com/admin/volunteer")
    return "Sent"