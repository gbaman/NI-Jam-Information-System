from flask_mail import Mail, Message
from flask import current_app as app
from secrets.config import email_username


def send_cookie_login_email(email_address, cookie):
    mail = Mail(app)
    with mail.connect() as conn:
        body = """
        Hey,
        
        A login link for your email address has been requested for the Mozfest Youth Zone volunteer system.
        If you requested this login link, click the link below. If you didn't request this login, please ignore this messsage.
        
        https://youth.gbaman.info/magic/{}
        
        -- Youth Zone team
        """.format(cookie)
        m = Message("Mozfest Youth Zone volunteer system login link", sender=["Mozfest Youth Zone login system", email_username], recipients=[email_address,], body=body)
        conn.send(m)
        print("Sending email to {} with login of http://127.0.0.1:5000/magic/{}".format(email_address, cookie))