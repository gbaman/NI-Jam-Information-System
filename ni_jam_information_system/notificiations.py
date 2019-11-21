import slack_messages
import database
import models
import configuration


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