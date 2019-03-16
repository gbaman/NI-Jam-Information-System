import time

from flask import Blueprint, render_template, request, make_response, redirect, flash, send_file, abort
import database
from datetime import datetime, timedelta
from secrets.config import *
import forms as forms
import logins
from decorators import *
import configuration
import google_sheets


trustee_routes = Blueprint('trustee_routes', __name__,
                           template_folder='templates')


@trustee_routes.route("/finance")
@trustee_required
def finance_home():
    return ""


@trustee_routes.route("/finance/ledger")
@trustee_required
def ledger():
    status, cookie = logins.validate_cookie(request.cookies.get('jam_login'))
    trustees = database.get_all_trustees()
    transactions = google_sheets.get_transaction_table(trustees=trustees)
    for transaction in transactions:
        transaction.user_id = cookie.user.user_id
    return render_template("trustee/ledger.html", transactions=transactions, trustees=trustees, container_name="container-wide")


@trustee_routes.route("/finance/ledger/payment_by/<transaction_id>")
@trustee_required
def ledger_payment_by_transaction(transaction_id):
    status, cookie = logins.validate_cookie(request.cookies.get('jam_login'))
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.PAYMENT_BY_ID, cookie.user.user_id)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.PAYMENT_BY, f"{cookie.user.first_name} {cookie.user.surname}")
    return redirect(url_for("trustee_routes.ledger"))


@trustee_routes.route("/finance/ledger/secondary_approved_by/<transaction_id>")
@trustee_required
def ledger_secondary_approved_by_transaction(transaction_id):
    status, cookie = logins.validate_cookie(request.cookies.get('jam_login'))
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.SECONDARY_APPROVED_ID, cookie.user.user_id)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.SECONDARY_APPROVED, f"{cookie.user.first_name} {cookie.user.surname}")
    return redirect(url_for("trustee_routes.ledger"))


@trustee_routes.route("/finance/ledger/verified_by/<transaction_id>")
@trustee_required
def ledger_verified_by_transaction(transaction_id):
    status, cookie = logins.validate_cookie(request.cookies.get('jam_login'))
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.VERIFIED_BY_ID, cookie.user.user_id)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.VERIFIED_BY, f"{cookie.user.first_name} {cookie.user.surname}")
    return redirect(url_for("trustee_routes.ledger"))


@trustee_routes.route("/finance/expenses_list")
@trustee_required
def expenses_list():
    expenses = google_sheets.get_volunteer_expenses_table()
    user = logins.get_current_user()
    for expense in expenses:
        expense.user_id = user.user_id
    return render_template("trustee/expenses_list.html", expenses=expenses)


# -------------- AJAX routes -------------


@trustee_routes.route("/finance/ledger/update_description_ajax", methods=['GET', 'POST'])
@trustee_required
def ledger_update_description():
    transaction_id = request.form['transaction_id']
    description = request.form['description']
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.DESCRIPTION, description)
    return ""


@trustee_routes.route("/finance/ledger/update_supplier_ajax", methods=['GET', 'POST'])
@trustee_required
def ledger_update_supplier():
    transaction_id = request.form['transaction_id']
    supplier = request.form['supplier']
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.SUPPLIER, supplier)
    return ""


@trustee_routes.route("/finance/ledger/update_notes_ajax", methods=['GET', 'POST'])
@trustee_required
def ledger_update_notes():
    transaction_id = request.form['transaction_id']
    notes = request.form['notes']
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.NOTES, notes)
    return ""


@trustee_routes.route("/finance/ledger/update_category_ajax", methods=['GET', 'POST'])
@trustee_required
def ledger_update_category():
    transaction_id = request.form['transaction_id']
    notes = request.form['category']
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.CATEGORY, notes)
    return ""


@trustee_routes.route("/finance/expenses_list/rejection_reason", methods=['GET', 'POST'])
@trustee_required
def expenses_list_rejection_reason():
    expense_id = request.form['expense_id']
    rejection_reason = request.form['rejection_reason']
    google_sheets.update_expense_cell(expense_id, google_sheets.E.REJECTION_REASON, rejection_reason)
    return ""