from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import Form, BooleanField, StringField, PasswordField, IntegerField, TextAreaField, RadioField, \
    SelectField, validators, HiddenField, FileField, DateTimeField, FloatField, DateTimeLocalField
from wtforms.fields import DateField
from wtforms_components import TimeField

from flask import g, Flask, current_app
import datetime

from database import get_volunteers_to_select, get_workshops_to_select, get_individual_time_slots_to_select, get_workshop_rooms, get_equipment_groups, get_all_equipment, get_all_badges, get_badge, get_workshop_from_workshop_id, CertificateTypeEnum
from models import FileTypeEnum


class CreateWorkshopForm(Form):
    workshop_title = StringField("Workshop title", [validators.DataRequired()])
    workshop_description = TextAreaField("Workshop description", [validators.DataRequired()])
    workshop_limit = IntegerField("Workshop max attendees", [validators.InputRequired()])
    workshop_level = RadioField("Workshop level", choices=[("Beginner", "Beginner"), ("Intermediate", "Intermediate"), ("Advanced", "Advanced"), ("Not taught", "Not taught")])
    workshop_url = StringField("Workshop URL (optional)", [validators.Optional(), validators.URL()])
    workshop_volunteer_requirements = IntegerField("Additional Volunteers needed per 10 attendees (optional)")
    workshop_id = HiddenField("Workshop ID", default="")


class AddWorkshopToJam(Form):
    workshop = SelectField("Workshop")
    volunteer = SelectField("Coordinator")
    slot = SelectField("Time slot")
    room = SelectField("Room")
    pilot = SelectField("Pilot", choices=[("False", "False"), ("True", "True")])
    pair = SelectField("Pairs required", choices=[("False", "False"), ("True", "True")])

    def __init__(self, *args, **kwargs):
        super(AddWorkshopToJam, self).__init__(*args, **kwargs)
        self.workshop.choices = [(workshop.workshop_id, workshop.workshop_name_file_status) for workshop in get_workshops_to_select()]
        self.volunteer.choices = [(-1, "None")] + get_volunteers_to_select()
        self.room.choices = get_workshop_rooms()
        self.slot.choices = get_individual_time_slots_to_select()
        self.room.choices = get_workshop_rooms()


class GetOrderIDForm(Form):
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
    dob = DateField("Date of Birth", [validators.DataRequired()])
    email = StringField("Email address - Note must be same used for Slack", [validators.DataRequired()])

    # Added ready to add to Login form itself on page.


class VolunteerAttendance(Form):
    attending_jam = SelectField("Attending Main Jam", choices=[("False", "False"), ("True", "True")])
    attending_setup = SelectField("Attending Setup", choices=[("False", "False"), ("True", "True")])
    attending_packdown = SelectField("Attending Packdown", choices=[("False", "False"), ("True", "True")])
    attending_food = SelectField("Attending Food After", choices=[("False", "False"), ("True", "True")])
    notes = TextAreaField("Notes")
    arrival_time = TimeField("Expected arrival time for Jam", default=datetime.time(hour=11, minute=0))


class ResetPasswordForm(Form):
    username = StringField("Username", [validators.DataRequired()])
    reset_code = StringField("Reset Code", [validators.DataRequired()])
    new_password = PasswordField("New Password", [validators.DataRequired()])


class UploadFileForm(FlaskForm):
    class Meta:
        csrf = False
    file_title = StringField("File title (optional)",)
    file_type = SelectField("Type of file being uploaded", validators=[validators.DataRequired()], coerce=int)
    file_permission = SelectField("Visibility level", choices=[("Public", "Public"), ("Jam team only", "Jam team only")])
    upload = FileField('File', validators=[
        FileRequired(),
        FileAllowed(("pdf", "ppt", "pptx", "py"), 'Should be a PDF or Powerpoint file!')
    ])
    
    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.file_type.choices = FileTypeEnum.dropdown_view()


class InventoryForm(Form):
    inventory_title = StringField("Inventory title", [validators.DataRequired()])


class AddEquipmentForm(Form):
    equipment_title = StringField("Equipment title", [validators.DataRequired()])
    equipment_code = StringField("Equipment code", [validators.DataRequired(), validators.Length(3, 3)])
    equipment_group = SelectField("Equipment group")

    def __init__(self, *args, **kwargs):
        super(AddEquipmentForm, self).__init__(*args, **kwargs)
        self.equipment_group.choices = [(str(group.equipment_group_id), group.equipment_group_name) for group in get_equipment_groups()]


class RoomForm(Form):
    room_id = HiddenField("Workshop room", default="")
    room_name = StringField("Room name", [validators.DataRequired()])
    room_capacity = IntegerField("Room capacity", [validators.DataRequired()])
    room_volunteers_needed = IntegerField("Room volunteers", [validators.DataRequired()])


class SlotForm(Form):
    slot_id = HiddenField("Workshop ID", default="")
    slot_time_start = TimeField("Slot time start", [validators.DataRequired()])
    slot_time_end = TimeField("Slot time finish", [validators.DataRequired()])
    slot_name = StringField("Slot Name")


class EquipmentAddToWorkshopForm(FlaskForm):
    equipment_name = SelectField("Equipment name")
    equipment_quantity_needed = IntegerField("Equipment quantity", [validators.DataRequired()])
    per_attendee = RadioField("Allocation", choices=[("True", "Per attendee"), ("False", "Shared equipment")])

    def __init__(self, *args, **kwargs):
        super(EquipmentAddToWorkshopForm, self).__init__(*args, **kwargs)
        self.equipment_name.choices = [(str(equipment.equipment_id), equipment.equipment_name) for equipment in get_all_equipment()]


class AddBadgeForm(FlaskForm):
    badge_id = HiddenField("Badge ID", default="")
    badge_name = StringField("Badge name", [validators.DataRequired()])
    badge_description = StringField("Badge description", [validators.DataRequired()])
    badge_required_non_core_count = IntegerField("Required number of non core dependencies badges", [validators.InputRequired()])


class AddBadgeDependencyForm(FlaskForm):
    badge_id = SelectField("Badge name", coerce=int)
    badge_awarded_core = SelectField("Core badge", choices=[("False", "False"), ("True", "True")])
    
    def __init__(self, *args, **kwargs):
        super(AddBadgeDependencyForm, self).__init__(*args, **kwargs)
        badge_choices = []
        parent_badge = get_badge(kwargs["badge_id"])
        for badge in get_all_badges(include_hidden=True):
            if badge.badge_id != int(parent_badge.badge_id) and not any(b.dependency_badge_id == badge.badge_id for b in parent_badge.badge_dependencies):
                badge_choices.append([badge.badge_id, badge.badge_name])
        self.badge_id.choices = badge_choices


class AddBadgeWorkshopForm(FlaskForm):
    badge_id = SelectField("Badge name", coerce=int)
    
    def __init__(self, *args, **kwargs):
        super(AddBadgeWorkshopForm, self).__init__(*args, **kwargs)
        badge_choices = []
        workshop = get_workshop_from_workshop_id(kwargs["workshop_id"])
        for badge in get_all_badges(include_hidden=True):
            if not any(b.badge_id == badge.badge_id for b in workshop.badges):
                badge_choices.append([badge.badge_id, badge.badge_name])
        self.badge_id.choices = badge_choices


class ExpensesClaimForm(FlaskForm):
    class Meta:
        csrf = False
    paypal_email_address = StringField("PayPal email address", [validators.Email(), validators.DataRequired()])
    requested_value = FloatField("Total cost being claimed for", [validators.DataRequired(), validators.NumberRange(min=0.01, max=100, message="Expense claims can only be up to £100")])
    receipt_date = DateField("Date on receipt", [validators.DataRequired()])
    expenses_type = SelectField("Expense type", [validators.DataRequired()], choices=[("Travel : Translink", "Travel : Translink"), ("Travel : Other", "Travel : Other"), ("Other Expense", "Other Expense")])
    receipt = FileField('Receipt', validators=[
        FileRequired(),
        FileAllowed(("pdf", "png", "jpg", "jpeg"), 'Should be a PDF, png, jpg or jpeg.')
    ])


class AddTransactionReceiptForm(FlaskForm):
    class Meta:
        csrf = False
    receipt_date = DateField("Date on receipt", [validators.DataRequired()])
    receipt = FileField('Receipt', validators=[
        FileRequired(),
        FileAllowed(("pdf", "png", "jpg", "jpeg"), 'Should be a PDF, png, jpg or jpeg.')
    ])


class UploadLedgerCSVForm(FlaskForm):
    class Meta:
        csrf = False
    csv_file = FileField('Bank CSV file', validators=[
        FileRequired(),
        FileAllowed(("csv",), 'Should be a CSV file from the bank.')
    ])


class PasswordResetForm(Form):
    email_address = StringField("Account email", [validators.DataRequired(), validators.Email()])
    maths = StringField("What is 5+5?", [validators.DataRequired()])


class ChangePasswordForm(Form):
    new_password = PasswordField("New password", [validators.DataRequired()])
    url_key = HiddenField()


class NewEventForm(Form):
    event_name = StringField("Event Name", [validators.DataRequired()])
    event_date = DateField("Event Date", [validators.DataRequired()])


class PoliceCheckForm(Form):
    certificate_type = SelectField("Select certificate type, default is DBS Update Service *", validators=[validators.DataRequired()], coerce=int)
    certificate_application_date = DateField("Application submitted date *", [validators.DataRequired()])
    certificate_reference = StringField("Certificate reference number")
    certificate_issue_date = DateField("Certificate issue date", validators=[validators.Optional()])
    certificate_expiry_date = DateField("Certificate Expiry date (usually 3 years after issue date)", validators=[validators.Optional()])
    certificate_table_id = HiddenField()

    def __init__(self, *args, **kwargs):
        super(PoliceCheckForm, self).__init__(*args, **kwargs)
        self.certificate_type.choices = CertificateTypeEnum.dropdown_view()


class AddLink(Form):
    link_short = StringField("Shortened link", [validators.DataRequired()])
    link_full = StringField("Full URL (including http:// or https://", [validators.DataRequired(), validators.URL()])


class AddMeeting(Form):
    meeting_name = StringField("Meeting name", [validators.DataRequired()])
    meeting_description = StringField("Meeting description", [validators.DataRequired()])
    meeting_location = StringField("Meeting location")
    meeting_start = DateTimeLocalField("Meeting start time", format='%Y-%m-%dT%H:%M')
    meeting_end = DateTimeLocalField("Meeting end time", format='%Y-%m-%dT%H:%M')