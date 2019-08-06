import database
import models
import google_sheets

import flask_mail

from flask import current_app as app

import configuration
from secrets import config


def send_email(login_user: models.LoginUser, subject, body):
    mail = flask_mail.Mail(app)
    with mail.connect() as conn:
        m = flask_mail.Message(subject, sender=[f"{configuration.verify_config_item('general', 'short_jam_organisation_name')} team", config.email_username], recipients=[login_user.email], body=body)
        conn.send(m)


def send_expenses_rejected_email(login_user: models.LoginUser, expense: google_sheets.Expense):
    email_body = f"""
    Hey {login_user.first_name},

    Your expenses request for {expense.value_symbol} submitted on {expense.expense_submit_date} has been rejected with the reason for
    "{expense.rejected_reason}"

    You can submit a new expense here - {configuration.verify_config_item("general", "base_url")}/admin/expenses_claim

    -- {configuration.verify_config_item("general", "short_jam_organisation_name")} team

    """

    send_email(login_user, "NIJIS expense rejected", email_body)
    
    
def send_expenses_paid_email(login_user: models.LoginUser, expense: google_sheets.Expense):
    email_body = f"""
    Hey {login_user.first_name},

    Your expenses request for {expense.value_symbol} submitted on {expense.expense_submit_date} has now been marked as paid out by {expense.paid_by}.

    -- {configuration.verify_config_item("general", "short_jam_organisation_name")} team

    """

    send_email(login_user, "NIJIS expense repaid", email_body)


def send_password_reset_email(login_user: models.LoginUser):
    print(f"Sending password reset email to {login_user.username}")
    database.generate_password_reset_url(login_user.user_id)
    email_body = f"""
    Hey {login_user.first_name},

    A password reset request has been put through for your account.
    If you did not request this, please let your NIJIS admin know right away.
    If on the other hand you did request it, please go to the following URL to reset your password

    {configuration.verify_config_item("general", "base_url")}/password_reset_url/{login_user.forgotten_password_url}

    Note - This URL will time out in 48 hours.

    -- {configuration.verify_config_item("general", "short_jam_organisation_name")} team
    """

    send_email(login_user, "NIJIS password reset request", email_body)


def send_password_reset_complete_email(login_user: models.LoginUser):
    print(f"Sending password reset complete email to {login_user.username}")
    email_body = f"""
    Hey {login_user.first_name},

    A password reset has been completed on your NIJIS account.
    If you requested this, please ignore this email.
    If though on the other hand, you did not, please let your NIJIS admin know ASAP!

    -- {configuration.verify_config_item("general", "short_jam_organisation_name")} team
    """

    send_email(login_user, "NIJIS password reset complete", email_body)