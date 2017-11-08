from wtforms import Form, BooleanField, StringField, PasswordField, IntegerField, TextAreaField, RadioField, SelectField, validators
from database import get_volunteers_to_select, get_workshops_to_select, get_individual_time_slots_to_select, get_workshop_rooms


class CreateWorkshopForm(Form):
    workshop_title = StringField("Workshop title", [validators.DataRequired()])
    workshop_description = TextAreaField("Workshop description", [validators.DataRequired()])
    workshop_limit = IntegerField("Workshop max attendees", [validators.DataRequired()])
    workshop_level = RadioField("Workshop level", choices=[("Beginner", "Beginner"), ("Intermediate", "Intermediate"), ("Advanced", "Advanced")])
    #workshop_time = RadioField("Workshop timeslot", choices=[("13:30-14:15", "13:30-14:15"), ("14:30-15:15", "14:30-15:15"), ("16:00-16:45", "16:00-16:45")])

class add_workshop_to_jam(Form):
    workshop = SelectField("Workshop", choices=get_workshops_to_select())
    volunteer = SelectField("Coordinator", choices=get_volunteers_to_select())
    slot = SelectField("Time slot", choices=get_individual_time_slots_to_select())
    room = SelectField("Room", choices=get_workshop_rooms())

    def __init__(self, *args, **kwargs):
        super(add_workshop_to_jam, self).__init__(*args, **kwargs)
        self.workshop.choices = get_workshops_to_select()
        self.volunteer.choices = get_volunteers_to_select()
        self.room.choices = get_workshop_rooms()


class get_order_ID_form(Form):
    order_id = IntegerField("Order ID", [validators.DataRequired()])
    day_password = StringField("Jam password", [validators.DataRequired()])


class LoginForm(Form):
    username = StringField("Username", [validators.DataRequired()])
    password = PasswordField("Password", [validators.DataRequired()])


class RegisterUserForm(Form):
    username = StringField("Username", [validators.DataRequired()])
    password = PasswordField("Password", [validators.DataRequired()])
    first_name = StringField("First name", [validators.DataRequired()])
    surname = StringField("Surname", [validators.DataRequired()])
    access_code = StringField("Access code", [validators.DataRequired()])

    # Added ready to add to Login form itself on page.