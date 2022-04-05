import datetime
import os
import uuid

from flask import Blueprint, render_template, request, make_response, redirect, flash, send_file
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import secure_filename

import database
import forms as forms
import eventbrite_interactions
import notificiations
from ast import literal_eval

import misc
import slack_messages
from decorators import *

admin_routes = Blueprint('admin_routes', __name__, template_folder='templates')


@admin_routes.route("/admin/import_attendees_from_eventbrite/<jam_id>")
@trustee_required
@module_core_required
def import_from_eventbrite(jam_id):
    database.update_attendees_from_eventbrite(jam_id)
    return redirect("/admin/manage_jams")


@admin_routes.route("/admin/admin_home")
@volunteer_required
@module_core_required
def admin_home():
    return render_template("admin/admin_home.html", selected_jam = database.get_jam_details(database.get_current_jam_id()))


@admin_routes.route("/admin/manage_jams", methods=['POST', 'GET'])
@trustee_required
@module_core_required
def manage_jams():
    form = forms.NewEventForm(request.form)
    if request.method == 'POST' and form.validate():
        database.add_standalone_event(form.event_name.data, form.event_date.data)
        return redirect(url_for("admin_routes.manage_jams"))
    return render_template("admin/manage_jams.html", form=form, jams=eventbrite_interactions.get_eventbrite_events_name_id(), jams_in_db=database.get_jams_in_db(), current_jam_id=database.get_current_jam_id())


@admin_routes.route("/admin/add_jam/<eventbrite_id>")
@trustee_required
@module_core_required
def add_jam_id(eventbrite_id):
    eventbrite_jam = eventbrite_interactions.get_eventbrite_event_by_id(eventbrite_id)
    database.add_eventbrite_jam(eventbrite_id, eventbrite_jam["name"]["text"], eventbrite_jam["start"]["local"].replace("T", " "))
    return redirect("/admin/manage_jams", code=302)


@admin_routes.route("/admin/delete_jam", methods=['POST', 'GET'])
@trustee_required
@module_core_required
def delete_jam():
    jam_id = request.form["jam_id"]
    if int(jam_id) == database.get_current_jam_id():
        print("Error, unable to remove Jam as is the current selected Jam {}".format(database.get_current_jam_id()))
        return
    print("Jam being deleted {}.".format(jam_id))
    database.remove_jam(jam_id)
    return " "


@admin_routes.route("/admin/select_jam", methods=['POST', 'GET'])
@trustee_required
@module_core_required
def select_jam():
    jam_id = request.form["jam_id"]
    if int(jam_id) == database.get_current_jam_id():
        print("Error, unable to select Jam as is the current selected Jam - {}".format(database.get_current_jam_id()))
        return
    print("Jam being selected {}.".format(jam_id))
    database.select_jam(int(jam_id))
    return " "


@admin_routes.route('/admin/manage_workshop_catalog/', methods=['GET', 'POST'])
@admin_routes.route('/admin/manage_workshop_catalog/<workshop_id>', methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def add_workshop_to_catalog(workshop_id = None):
    form = forms.CreateWorkshopForm(request.form)
    if workshop_id and request.method == "GET":
        workshop = database.get_workshop_from_workshop_id(workshop_id)
        form.workshop_title.default = workshop.workshop_title
        form.workshop_description.default = workshop.workshop_description
        form.workshop_limit.default = workshop.workshop_limit
        form.workshop_level.default = workshop.workshop_level
        form.workshop_url.default = workshop.workshop_url
        form.workshop_id.default = workshop.workshop_id
        form.workshop_volunteer_requirements.default = workshop.workshop_volunteer_requirements
        form.process()
    if request.method == 'POST' and form.validate():
        database.add_workshop(form.workshop_id.data, form.workshop_title.data, form.workshop_description.data, form.workshop_limit.data, form.workshop_level.data, form.workshop_url.data, form.workshop_volunteer_requirements.data)
        return redirect(url_for('admin_routes.add_workshop_to_catalog'))
    return render_template('admin/manage_workshop_catalog.html', form=form, workshops=database.get_workshops_to_select())


@admin_routes.route('/admin/add_workshop_to_jam', methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def add_workshop_to_jam():
    form = forms.AddWorkshopToJam(request.form)
    if request.method == 'POST':# and form.validate():
        workshop = database.add_workshop_to_jam_from_catalog(database.get_current_jam_id(), form.workshop.data, form.volunteer.data, form.slot.data, form.room.data, int(literal_eval(form.pilot.data)), int(literal_eval(form.pair.data)))
        if form.volunteer.data:
            user = database.get_login_user_from_user_id(form.volunteer.data)
            if user and user != request.logged_in_user:
                notificiations.send_workshop_signup_full_notification(user, request.logged_in_user, workshop)
        return redirect("/admin/add_workshop_to_jam", code=302)
    return render_template('admin/add_workshop_to_jam_form.html', form=form, workshop_slots=database.get_schedule_by_time_slot(database.get_current_jam_id(), 0, admin=True))


@admin_routes.route('/admin/delete_workshop/<workshop_id>')
@volunteer_required
@module_workshops_required
def delete_workshop(workshop_id):
    database.delete_workshop(workshop_id)
    return redirect(('admin/manage_workshop_catalog'))


@admin_routes.route('/admin/archive_workshop/<workshop_id>')
@volunteer_required
@module_workshops_required
def archive_workshop(workshop_id):
    database.archive_workshop(workshop_id)
    return redirect(('admin/manage_workshop_catalog'))


@admin_routes.route('/admin/workshops', methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def admin_workshops():
    return render_template('admin/admin_workshops.html')


@admin_routes.route("/admin/manage_users", methods=['GET', 'POST'])
@trustee_required
@module_core_required
def manage_users():
    users = database.get_users(include_inactive=True)
    users = sorted(users, key=lambda x: x.active, reverse=True)
    return render_template("admin/manage_users.html", users=users)


@admin_routes.route("/admin/attendee_list")
@volunteer_required
@module_attendees_required
def attendee_list():
    jam_attendees = database.get_all_attendees_for_jam(database.get_current_jam_id())
    return render_template("admin/attendee_list.html", attendees=jam_attendees)


@admin_routes.route("/admin/volunteer")
@admin_routes.route("/admin/volunteer/<user_id>")
@volunteer_required
@module_volunteer_signup_required
def volunteer(user_id=None):
    selected_jam = database.get_jam_details(database.get_current_jam_id())
    validated_user = request.logged_in_user
    if user_id and not request.logged_in_user.user_id == user_id:
        if request.logged_in_user.group_id >=4:
            validated_user = database.get_login_user_from_user_id(user_id)
            if not validated_user:
                return "Error, user not found..."
    if not validated_user.ics_uuid:
        database.reset_login_user_ics_uuid(validated_user)
    time_slots, workshop_rooms_in_use = database.get_volunteer_data(database.get_current_jam_id(), validated_user)
    users = database.get_users(include_inactive=False)
    return render_template("admin/volunteer_signup.html", time_slots = time_slots, workshop_rooms_in_use = workshop_rooms_in_use, current_selected = ",".join(str(x.workshop_run_id) for x in validated_user.workshop_runs) +",", user=validated_user, users=users, jam_id=selected_jam.jam_id, selected_jam=selected_jam)


@admin_routes.route("/admin/volunteer_attendance", methods=['GET', 'POST'])
@admin_routes.route("/admin/volunteer_attendance/<event_id>", methods=['GET', 'POST'])
@volunteer_required
@module_volunteer_signup_required
def volunteer_attendance(event_id=None):
    if event_id:
        event_id = database.get_jam_details(event_id).jam_id
    else:
        event_id = database.get_current_jam_id()
    volunteer_attendances, stats = database.get_attending_volunteers(event_id)
    user = database.get_user_from_cookie(request.cookies.get('jam_login'))
    user_filled_in = True
    for checking_user in volunteer_attendances:
        if checking_user.user_id == user.user_id and not checking_user.attend:
            user_filled_in = False
            break
    form = forms.VolunteerAttendance(request.form)
    if request.method == 'POST' and form.validate():
        database.add_volunteer_attendance(event_id, request.logged_in_user.user_id, int(literal_eval(form.attending_jam.data)), int(literal_eval(form.attending_setup.data)), int(literal_eval(form.attending_packdown.data)), int(literal_eval(form.attending_food.data)), form.notes.data, form.arrival_time.data)

        return redirect((f"/admin/volunteer_attendance{ f'/{event_id}' if event_id else ''}"), code=302)
    return render_template("admin/volunteer_attendance.html", form=form, volunteer_attendances=volunteer_attendances, user_id=request.logged_in_user.user_id, selected_jam=database.get_jam_details(event_id), stats=stats, last_slack_reminder=database.get_configuration_item("slack_reminder_sent"), user_filled_in=user_filled_in)


@admin_routes.route("/admin/manage_attendees")
@volunteer_required
@module_attendees_required
def manage_attendees():
    # Getting names of users and also volunteers that are down as attending this Jam
    jam_attendees = database.get_all_attendees_for_jam(database.get_current_jam_id())
    volunteer_attendances, stats = database.get_attending_volunteers(database.get_current_jam_id(), only_attending_volunteers=True)
    for volunteer_attendee in volunteer_attendances:

        for volunteer_attendee_record in volunteer_attendee.attending:
            if volunteer_attendee_record.jam_id == database.get_current_jam_id():
                volunteer_attendee.current_jam = volunteer_attendee_record
                break
        volunteer_attendee.current_location = volunteer_attendee.current_jam.current_location
        volunteer_attendee.attendee_id = volunteer_attendee.user_id
        volunteer_attendee.order_id = "Volunteer"
        volunteer_attendee.attendee_login = ""
        jam_attendees.append(volunteer_attendee)
    for attendee in jam_attendees:
        if attendee.current_location == "Checked in":
            attendee.bg_colour = database.green
        elif attendee.current_location == "Checked out":
            attendee.bg_colour = database.yellow
        elif attendee.current_location == "Not arrived":
            attendee.bg_colour = database.light_grey

    jam_attendees = sorted(jam_attendees, key=lambda x: x.current_location, reverse=False)
    attendee_logins = database.get_attendee_logins()
    return render_template("admin/manage_attendees.html", attendees=jam_attendees, attendee_logins=attendee_logins)


@admin_routes.route("/admin/fire_list")
@volunteer_required
@module_attendees_required
def fire_list():
    jam_attendees = database.get_all_attendees_for_jam(database.get_current_jam_id())
    volunteer_attendances, stats = database.get_attending_volunteers(database.get_current_jam_id(),
                                                              only_attending_volunteers=True)
    for volunteer_attendee in volunteer_attendances:

        for volunteer_attendee_record in volunteer_attendee.attending:
            if volunteer_attendee_record.jam_id == database.get_current_jam_id():
                volunteer_attendee.current_jam = volunteer_attendee_record
                break
        if volunteer_attendee.current_jam.current_location != "Checked in":
            continue  # If volunteer is not marked as checked in, ignore them
        volunteer_attendee.current_location = volunteer_attendee.current_jam.current_location
        volunteer_attendee.attendee_id = volunteer_attendee.user_id
        volunteer_attendee.order_id = "Volunteer"
        jam_attendees.append(volunteer_attendee)
    return render_template("admin/fire_list.html", attendees=jam_attendees)


@admin_routes.route("/admin/workshop_details/<workshop_id>", methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def workshop_details(workshop_id):
    file_form = forms.UploadFileForm(CombinedMultiDict((request.files, request.form)))
    if file_form.validate_on_submit():
        f = file_form.upload.data
        print(f.filename)
        filename = secure_filename(f.filename)
        base_dir = "static/files/{}".format(workshop_id)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        file_path = "{}/{}".format(base_dir, filename)
        if not os.path.isfile(file_path):
            f.save(file_path)
            if request.form['file_title']:
                file_title = request.form['file_title']
            else:
                file_title = secure_filename(f.filename)
            database.add_workshop_file(file_title, file_path, request.form['file_permission'], request.form['file_type'], workshop_id)
            flash("File upload successful.", "success")
        else:
            flash("Failed to upload - File of same name already exists.", "danger")
        return redirect(url_for('admin_routes.workshop_details', workshop_id=workshop_id))

    equipment_form = forms.EquipmentAddToWorkshopForm()
    if equipment_form.validate_on_submit():
        equipment_id = int(request.form['equipment_name'])
        equipment_quantity = int(request.form['equipment_quantity_needed'])
        per_attendee = False
        if request.form['per_attendee'] == "True": per_attendee = True
        database.add_equipment_to_workshop(equipment_id, workshop_id, equipment_quantity, per_attendee)

    badge_form = forms.AddBadgeWorkshopForm(workshop_id=workshop_id)
    if badge_form.validate_on_submit():
        badge_id = int(request.form['badge_id'])
        database.add_badge_to_workshop(workshop_id, badge_id)
        return redirect(url_for('admin_routes.workshop_details', workshop_id=workshop_id))

    workshop = database.get_workshop_from_workshop_id(workshop_id)
    return render_template("admin/workshop_details.html", workshop=workshop, file_form=file_form, equipment_form=equipment_form, equipments=database.get_all_equipment_for_workshop(workshop_id), badge_form=badge_form)


@admin_routes.route("/admin/delete_workshop_file/<file_id>")
@volunteer_required
@module_workshops_required
def delete_workshop_file(file_id):
    workshop_id = database.remove_workshop_file(file_id)
    flash("File has been removed.", category="success")
    return redirect("/admin/workshop_details/{}".format(workshop_id), code=302)


@admin_routes.route("/admin/delete_workshop_equipment/<equipment_id>/<workshop_id>")
@volunteer_required
@module_workshops_required
def delete_workshop_equipment(equipment_id, workshop_id):
    database.remove_workshop_equipment(equipment_id, workshop_id)
    flash("Equipment has been removed.", category="success")
    return redirect("/admin/workshop_details/{}".format(workshop_id), code=302)


@admin_routes.route("/admin/manage_inventories", methods=['GET', 'POST'])
@volunteer_required
@module_equipment_required
def manage_inventories():
    form = forms.InventoryForm(request.form)
    if request.method == 'POST' and form.validate():
        if database.add_inventory(request.form['inventory_title']):
            return redirect(url_for("admin_routes.manage_inventories"))
        flash("Unable to add a new inventory with the name '{}' because one with that name already exists.".format(request.form['inventory_title']), "danger")
        return redirect(url_for("admin_routes.manage_inventories"))
    current_inventoy = database.get_configuration_item("current_inventory")
    if current_inventoy:
        current_inventoy = int(current_inventoy)
    return render_template("admin/manage_inventories.html", form=form, inventories = database.get_inventories(), current_selected_inventory=current_inventoy)


@admin_routes.route("/admin/manage_inventory/<inventory_id>")
@volunteer_required
@module_equipment_required
def manage_inventory(inventory_id):
    equipment = database.get_all_equipment(manual_add_only=False)
    return render_template("admin/inventory.html", equipment=equipment)


@admin_routes.route("/admin/manage_equipment", methods=['GET', 'POST'])
@volunteer_required
@module_equipment_required
def manage_equipment():
    form = forms.AddEquipmentForm(request.form)
    if request.method == 'POST' and form.validate():
        if not database.add_equipment(form.equipment_title.data, form.equipment_code.data, form.equipment_group.data):
            flash("Unable to add equipment.", "danger")
        return redirect(url_for("admin_routes.manage_equipment"))
    return render_template("admin/manage_equipment.html", form=form, equipment=database.get_all_equipment())


@admin_routes.route("/admin/wrangler_overview_legacy", methods=['GET', 'POST'])
@volunteer_required
@module_volunteer_signup_required
def wrangler_overview():
    return render_template("admin/wrangler_overview_legacy.html", jam_id=database.get_current_jam_id(), raspberry_jam=database.get_jam_details(database.get_current_jam_id()).name, slots=database.get_wrangler_overview(database.get_current_jam_id()))


@admin_routes.route("/admin/wrangler_overview", methods=['GET', 'POST'])
@volunteer_required
@module_volunteer_signup_required
def wrangler_overview_equipment():
    return render_template("admin/wrangler_overview_equipment.html", jam_id=database.get_current_jam_id(), raspberry_jam=database.get_jam_details(database.get_current_jam_id()).name, slots=database.get_wrangler_overview(database.get_current_jam_id()))


@admin_routes.route('/admin/jam_setup', methods=['GET', 'POST'])
@admin_routes.route('/admin/jam_setup/slot/<slot_id>', methods=['GET', 'POST'])
@admin_routes.route('/admin/jam_setup/room/<room_id>', methods=['GET', 'POST'])
@trustee_required
@module_workshops_required
def jam_setup(slot_id=None, room_id=None):
    room_form = forms.RoomForm(request.form)
    slot_form = forms.SlotForm(request.form)
    if slot_id and request.method == "GET":
        slot = database.get_time_slots_objects().filter(database.WorkshopSlot.slot_id == slot_id).first()
        slot_form.slot_time_start.default = slot.slot_time_start
        slot_form.slot_time_end.default = slot.slot_time_end
        slot_form.slot_name.default = slot.slot_name
        slot_form.slot_id.default = slot.slot_id
        slot_form.process()
    elif room_id and request.method == "GET":
        room = database.get_workshop_rooms_objects().filter(database.WorkshopRoom.room_id == room_id).first()
        room_form.room_name.default = room.room_name
        room_form.room_capacity.default = room.room_capacity
        room_form.room_volunteers_needed.default = room.room_volunteers_needed
        room_form.room_id.default = room.room_id
        room_form.process()
    if request.method == 'POST' and (slot_form.validate()):
        if slot_form.slot_time_start.data < slot_form.slot_time_end.data:
            database.add_slot(slot_form.slot_id.data, slot_form.slot_time_start.data, slot_form.slot_time_end.data, slot_form.slot_name.data)
        else:
            flash("Error - Start time is after end time!", "danger")
        return redirect(('/admin/jam_setup'))
    elif request.method == 'POST' and room_form.validate():
        if not database.add_workshop_room(room_id, room_form.room_name.data, room_form.room_capacity.data, room_form.room_volunteers_needed.data):
            flash("Error - Unable to add new workshop room. Does a workshop already exist with that name?", "danger")
    return render_template('admin/jam_setup.html', form_room=room_form, form_slot=slot_form, rooms=database.get_workshop_rooms_objects(), slots=database.get_time_slots_objects())


@admin_routes.route('/admin/jam_setup/remove_slot/<slot_id>', methods=['GET', 'POST'])
@trustee_required
@module_core_required
def remove_slot(slot_id):
    database.remove_slot(slot_id)
    flash("Slot removed.", "success")
    return redirect(('/admin/jam_setup'))


@admin_routes.route('/admin/jam_setup/remove_workshop_room/<room_id>', methods=['GET', 'POST'])
@trustee_required
@module_core_required
def remote_workshop_room(room_id):
    database.remove_room(room_id)
    flash("Room removed.", "success")
    return redirect(('/admin/jam_setup'))


@admin_routes.route('/admin/badge', methods=['GET', 'POST'])
@admin_routes.route('/admin/badge/<int:badge_id>', methods=['GET', 'POST'])
@volunteer_required
@module_badge_required
def badge_catalog(badge_id=None):
    form = forms.AddBadgeForm(request.form)
    if badge_id and request.method == 'GET':
        badge = database.get_badge(badge_id)
        form.badge_id.default = badge.badge_id
        form.badge_name.default = badge.badge_name
        form.badge_description.default = badge.badge_description
        form.badge_required_non_core_count.default = badge.badge_children_required_count
        form.process()
    elif request.method == 'POST' and form.validate():
        if not database.add_badge(form.badge_id.data, form.badge_name.data, form.badge_description.data, form.badge_required_non_core_count.data):
            flash("Unable to add/edit badge.", "danger")
        return redirect(url_for("admin_routes.badge_catalog"))
    form.badge_id.default = -1
    return render_template("admin/badge_catalog.html", form=form, badges=database.get_all_badges())


@admin_routes.route('/admin/badge/edit/<badge_id>', methods=['GET', 'POST'])
@volunteer_required
@module_badge_required
def badge_edit(badge_id):
    form = forms.AddBadgeDependencyForm(request.form, badge_id = int(badge_id))
    if request.method == 'POST' and form.validate():
        if not database.add_badge_dependency(badge_id, form.badge_id.data, int(literal_eval(form.badge_awarded_core.data))):
            flash("Unable to add badge dependency.", "danger")
        else:
            flash("Badge dependency added.", "success")
        return redirect(url_for("admin_routes.badge_edit", badge_id=badge_id))
    return render_template("admin/badge_edit.html", form=form, badge=database.get_badge(badge_id))


@admin_routes.route('/admin/badge/remove_workshop_requirement/<badge_id>/<workshop_id>')
@volunteer_required
@module_badge_required
def remove_badge_workshop_requirement(badge_id, workshop_id):
    database.remove_badge_workshop_requirement(workshop_id, badge_id)
    return redirect(url_for("admin_routes.workshop_details", workshop_id=workshop_id))


@admin_routes.route('/admin/badge/remove_badge_dependency/<badge_id>/<dependency_badge_id>')
@volunteer_required
@module_badge_required
def remove_badge_dependency(badge_id, dependency_badge_id):
    database.remove_badge_dependency(badge_id, dependency_badge_id)
    return redirect(url_for("admin_routes.badge_edit", badge_id=badge_id))


@admin_routes.route("/admin/expenses_claim", methods=['GET', 'POST'])
@volunteer_required
@module_equipment_required
def expenses_claim():
    import google_sheets
    form = forms.ExpensesClaimForm(CombinedMultiDict((request.files, request.form)))
    if form.validate_on_submit():
        f = form.receipt.data
        month_year = form.receipt_date.data.strftime("%B-%Y").lower()
        file_type = f.filename.split(".")[-1]
        file_uuid = str(uuid.uuid4())[0:8]
        filename = f"{file_uuid}.{file_type}"
        user = logins.get_current_user()
        base_dir = f"static/files/expenses/{month_year}-{user.username}"
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        file_path = f"{base_dir}/{filename}"
        if not os.path.isfile(file_path):
            f.save(file_path)
            flash("File upload successful.", "success")
            expense = google_sheets.Expense(["", datetime.datetime.today().strftime("%d/%m/%Y"), form.receipt_date.data.strftime("%d/%m/%Y"), user.user_id, f"{user.first_name} {user.surname}", form.paypal_email_address.data, f"/{file_path}", form.requested_value.data, None, None, None, None, None, None, None, None, form.expenses_type.data], offset=0)
            google_sheets.create_expense_row(expense)
        else:
            flash("Failed to upload - File of same name already exists.", "danger")

        return redirect(url_for("admin_routes.expenses_claim"))
    expenses = google_sheets.get_volunteer_expenses_table()
    user_expenses = []
    for expense in expenses:
        if int(expense.volunteer_id) == logins.get_current_user().user_id:
            user_expenses.append(expense)
    if user_expenses:
        form.paypal_email_address.default = user_expenses[-1].paypal_email
        form.process()

    return render_template("admin/expenses_claims.html", form=form, expenses=user_expenses)


@admin_routes.route("/static/files/expenses/<folder>/<filename>")
@volunteer_required
@module_finance_required
def files_download(folder, filename):
    return send_file(f"static/files/expenses/{folder}/{filename}")


@admin_routes.route("/admin/workshop_run/<workshop_run_id>")
@volunteer_required
@module_badge_required
def workshop_run_details(workshop_run_id):
    jam_workshop = database.get_workshop_run(int(workshop_run_id))
    return render_template("admin/workshop_run_details.html", jam_workshop=jam_workshop, attendee_logins=database.get_attendee_logins())


@admin_routes.route("/admin/attendee_login_info/<attendee_login_id>")
@volunteer_required
@module_attendees_required
def attendee_login_info(attendee_login_id):
    badges = database.get_all_badges(include_hidden=True)
    attendee_login = database.get_attendee_login_from_attendee_login_id(attendee_login_id)
    return render_template("admin/attendee_login_info.html", attendee_login=attendee_login, badges=badges)


@admin_routes.route("/admin/police_checks", methods=['GET', 'POST'])
@admin_routes.route("/admin/police_checks/<certificate_table_id>", methods=['GET', 'POST'])
@volunteer_required
@module_police_check_required
def police_check(certificate_table_id=None):
    police_checks_in_db = database.get_police_checks_for_user(request.logged_in_user.user_id)
    form = forms.PoliceCheckForm(request.form)
    if request.method == 'POST' and form.validate():
        database.update_police_check(request.logged_in_user,
                                     form.certificate_table_id.data,
                                     form.certificate_type.data,
                                     form.certificate_application_date.data,
                                     form.certificate_reference.data,
                                     form.certificate_issue_date.data,
                                     form.certificate_expiry_date.data
                                     )
        return redirect(url_for("admin_routes.police_check"))
    if certificate_table_id:
        edit_police_check = database.get_police_check_single(request.logged_in_user.user_id, certificate_table_id)
        if edit_police_check:
            form.certificate_table_id.default = edit_police_check.certificate_table_id
            form.certificate_type.default = edit_police_check.certificate_type.value
            form.certificate_application_date.default = edit_police_check.certificate_application_date
            form.certificate_reference.default = edit_police_check.certificate_reference
            form.certificate_issue_date.default = edit_police_check.certificate_issue_date
            form.certificate_expiry_date.default = edit_police_check.certificate_expiry_date
            form.process()
    return render_template("admin/police_checks.html", form=form, police_checks=police_checks_in_db)


@admin_routes.route("/admin/verify_police_check/<certificate_table_id>")
@volunteer_required
@module_police_check_required
def verify_police_check(certificate_table_id):
    database.verify_dbs_update_service_certificate(request.logged_in_user, certificate_table_id)
    return redirect(misc.redirect_url())


@admin_routes.route("/admin/remove_police_check/<certificate_table_id>")
@volunteer_required
@module_police_check_required
def remove_police_check(certificate_table_id):
    database.remove_police_check(request.logged_in_user, certificate_table_id)
    return redirect(misc.redirect_url())


####################################### AJAX Routes #######################################




@admin_routes.route("/admin/get_password_reset_code_ajax", methods=['GET', 'POST'])
@super_admin_required
@module_core_required
def get_password_reset_code():
    user_id = request.form['user_id']
    reset_code = database.get_user_reset_code(user_id)
    return "The requested password reset code is - {}".format(reset_code)


@admin_routes.route("/admin/upgrade_to_volunteer_permission_ajax", methods=['GET', 'POST'])
@super_admin_required
@module_core_required
def upgrade_user_permission():
    user_id = request.form['user_id']
    database.set_group_for_user(user_id, 3)
    return ""


@admin_routes.route("/admin/disable_volunteer_account_ajax", methods=['GET', 'POST'])
@super_admin_required
@module_core_required
def disable_volunteer_account():
    user_id = request.form['user_id']
    database.enable_user(user_id, False)
    return ""


@admin_routes.route("/admin/enable_volunteer_account_ajax", methods=['GET', 'POST'])
@super_admin_required
@module_core_required
def enable_volunteer_account():
    user_id = request.form['user_id']
    database.enable_user(user_id, True)
    return ""


@admin_routes.route("/admin/modify_workshop_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def modify_workshop_ajax():
    workshop_id = request.form['workshop_id']
    attendee_id = request.form['attendee_id']
    status, message = database.add_attendee_to_workshop(database.get_current_jam_id(), attendee_id, workshop_id)
    if status:
        return ("")


@admin_routes.route("/admin/delete_workshop_from_jam_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_workshops_required
def delete_workshop_from_jam_ajax():
    workshop_id = request.form['workshop_id']
    database.remove_workshop_from_jam(workshop_id)
    return redirect("/admin/add_workshop_to_jam", code=302)


@admin_routes.route("/admin/check_out_attendee_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_attendees_required
def check_out_attendee_ajax():
    attendee_id = request.form['attendee_id']
    database.check_out_attendee(attendee_id)
    return redirect("/admin/manage_attendees", code=302)


@admin_routes.route("/admin/check_in_attendee_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_attendees_required
def check_in_attendee_ajax():
    attendee_id = request.form['attendee_id']
    database.check_in_attendee(attendee_id)
    return " "


@admin_routes.route("/admin/volunteer_update_ajax/<user_id>", methods=['GET', 'POST'])
@volunteer_required
@module_volunteer_signup_required
def update_volunteer(user_id):
    new_sessions = request.json
    sessions = []
    validated_user = request.logged_in_user
    if user_id != str(request.logged_in_user) and request.logged_in_user.group_id >= 4:
        validated_user = database.get_login_user_from_user_id(user_id)
    for session in new_sessions:
        if len(session) > 0:
            sessions.append(int(session))
    if database.set_user_workshop_runs_from_ids(validated_user, database.get_current_jam_id(), sessions):
        if validated_user != request.logged_in_user:
            notificiations.send_workshop_signup_notification(validated_user, request.logged_in_user)
        return "True"


@admin_routes.route("/admin/update_attendee_info_ajax", methods=['GET', 'POST'])
@volunteer_required
@module_core_required
def update_attendee_info():
    current_jam = database.get_current_jam_id()
    if database.update_attendees_from_eventbrite(current_jam):
        return " "
    else:
        return "Jam not enabled for Eventbrite, so no attendees to import."


@admin_routes.route("/admin/select_inventory_ajax", methods=['GET', 'POST'])
@trustee_required
@module_equipment_required
def select_inventory():
    inventory_id = int(request.form['inventory_id'])
    database.set_configuration_item("current_inventory", inventory_id)
    return ""


@admin_routes.route("/admin/get_inventory_equipment", methods=['GET', 'POST'])
@volunteer_required
@module_equipment_required
def get_inventory_equipment():
    inventory_id = int(request.form['inventory_id'])
    equipment = database.get_equipment_in_inventory(inventory_id)
    to_send = ([dict(equipment_id=e.equipment_id, equipment_name=e.equipment_name, equipment_code=e.equipment_code, total_quantity=e.total_quantity, equipment_entries=[dict(equipment_entry_id=ee.equipment_entry_id, equipment_entry_number=str(ee.equipment_entry_number).zfill(3), equipment_quantity=ee.equipment_quantity) for ee in e.equipment_entries]) for e in equipment])
    return json.dumps(to_send)


@admin_routes.route("/admin/add_inventory_equipment_entry", methods=['GET', 'POST'])
@volunteer_required
@module_equipment_required
def add_inventory_equipment_entry():
    inventory_id = int(request.form['inventory_id'])
    equipment_entry_id = int(request.form['equipment_entry_id'])
    entry_quantity = int(request.form['entry_quantity'])
    database.add_equipment_entry_to_inventory(int(inventory_id), int(equipment_entry_id), int(entry_quantity))
    return ""


@admin_routes.route("/admin/add_inventory_equipment_entry_manual", methods=['GET', 'POST'])
@volunteer_required
@module_equipment_required
def add_inventory_equipment_entry_manual():
    inventory_id = int(request.form['inventory_id'])
    equipment_id = int(request.form['equipment_id'])
    entry_quantity = int(request.form['entry_quantity'])
    database.add_equipment_quantity_to_inventory(inventory_id, equipment_id, entry_quantity)
    return ""


@admin_routes.route("/admin/remove_inventory_equipment_entry", methods=['GET', 'POST'])
@volunteer_required
@module_equipment_required
def remove_inventory_equipment_entry():
    inventory_id = int(request.form['inventory_id'])
    equipment_entry_id = int(request.form['equipment_entry_id'])
    database.remove_equipment_entry_to_inventory(int(inventory_id), int(equipment_entry_id))
    return ""


@admin_routes.route("/admin/update_workshop_badge_award", methods=['GET', 'POST'])
@volunteer_required
@module_badge_required
def update_workshop_badge_award(): # Handle both if an attendee_id is provided or an attendee_login_id
    attendee_id = request.form['attendee_id']
    attendee_login_id = request.form['attendee_login_id']
    badge_id = request.form['badge_id']
    if attendee_id: # If attendee_id
        attendee_login = database.get_attendee_login_from_attendee_id(int(attendee_id))
    elif attendee_login_id: # If attendee_login_id
        attendee_login = database.get_attendee_login_from_attendee_login_id(int(attendee_login_id))
    else:
        attendee_login = None
    if database.update_workshop_badge_award(attendee_login, badge_id):
        return ""


@admin_routes.route("/admin/ajax_recalculate_badges", methods=['GET', 'POST'])
@volunteer_required
@module_badge_required
def recalculate_badges():
    if database.update_badges_for_all_attendees():
        return ""
    
    
@admin_routes.route("/admin/update_jam_password_ajax", methods=['GET', 'POST'])
@trustee_required
@module_core_required
def update_jam_password():
    jam_id = int(request.form["jam_id"])
    jam_password = request.form["jam_password"]
    database.set_jam_password(jam_id, jam_password)
    return " "


@admin_routes.route("/admin/verify_dob_in_system", methods=['GET', 'POST'])
@volunteer_required
@module_core_required
def verify_dob_in_system():
    user: database.LoginUser = request.logged_in_user
    if user.date_of_birth:
        return "true"
    return "false"


@admin_routes.route("/admin/update_dob_in_system", methods=['GET', 'POST'])
@volunteer_required
@module_core_required
def update_dob_in_system():
    user: database.LoginUser = request.logged_in_user
    date_of_birth = request.form["dob"]
    try:
        converted_date_of_birth = datetime.datetime.strptime(date_of_birth, "%d/%m/%Y")
        database.update_login_user_date_of_birth(user, converted_date_of_birth)
        return " "
    except ValueError:
        pass
