from wtforms import Form, BooleanField, StringField, PasswordField, IntegerField, TextAreaField, RadioField, SelectField, validators
from ni_jam_information_system.database import get_volunteers_to_select, get_workshops_to_select


class CreateWorkshopForm(Form):
    workshop_title = StringField("Workshop title", [validators.DataRequired()])
    workshop_description = TextAreaField("Workshop description", [validators.DataRequired()])
    workshop_limit = IntegerField("Workshop max attendees", [validators.DataRequired()])
    workshop_level = RadioField("Workshop level", choices=[("Beginner", "Beginner"), ("Intermediate", "Intermediate"), ("Advanced", "Advanced")])
    #workshop_time = RadioField("Workshop timeslot", choices=[("13:30-14:15", "13:30-14:15"), ("14:30-15:15", "14:30-15:15"), ("16:00-16:45", "16:00-16:45")])

class add_workshop_to_jam(Form):
    workshop = SelectField("Workshop", choices=get_workshops_to_select())
    volunteer = SelectField("Coordinator", choices=get_volunteers_to_select())
    #slot = SelectField("Time slot", choices=)


class get_order_ID_form(Form):
    order_id = IntegerField("Order ID", [validators.DataRequired()])