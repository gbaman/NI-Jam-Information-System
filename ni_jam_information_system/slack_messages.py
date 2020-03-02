import slack

import configuration
from secrets import config
import models
from typing import List


def _setup_slack_client() -> slack.WebClient:
    client = slack.WebClient(config.slack_token)
    return client


def _get_user_id_from_email(users, email):
    for user in users:
        if "profile" in user and "email" in user["profile"]:
            if user["profile"]["email"] == email:
                return user["id"]
    return False


def send_slack_direct_message(users: List[models.LoginUser], message):
    if not configuration.verify_modules_enabled().module_slack:
        return
    client = _setup_slack_client()
    slack_users = client.users_list()["members"]
    for user in users:
        user_id = _get_user_id_from_email(slack_users, user.email)
        if user_id:
            # c = client.conversations_open(users=[user_id]) # Not sure if this is actually needed anymore?
            try:
                client.chat_postMessage(channel=user_id, text=message, as_user="true")
                print(f"Slack Message sent to {user.first_name} {user.surname} with message of \"{message[:40]}\"...")
            except Exception as e:
                print(e)
                print(f"Unable to send Slack message to {user.first_name} {user.surname}.")