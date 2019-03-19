import os
import uuid

from flask import Blueprint, render_template, request, make_response, redirect, flash, send_file, abort
from werkzeug.datastructures import CombinedMultiDict

import database
from datetime import datetime
import forms as forms
from decorators import *
import configuration
if configuration.verify_modules_enabled().module_finance:
    import google_sheets


trustee_routes = Blueprint('trustee_routes', __name__,
                           template_folder='templates')


@trustee_routes.route("/finance")
@trustee_required
def finance_home():
    return ""


@trustee_routes.route("/finance/ledger")
@trustee_required
@module_finance_required
def ledger():
    status, cookie = logins.validate_cookie(request.cookies.get('jam_login'))
    volunteers = database.get_users(include_inactive=True)
    base_transactions = google_sheets.get_transaction_table(logins=volunteers)
    transactions = []
    for transaction in base_transactions:
        if transaction.bank_date:
            transaction.user_id = cookie.user.user_id
            transactions.append(transaction)
    return render_template("trustee/ledger.html", transactions=transactions, trustees=volunteers, container_name="container-wide")


@trustee_routes.route("/finance/ledger/payment_by/<transaction_id>")
@trustee_required
@module_finance_required
def ledger_payment_by_transaction(transaction_id):
    status, cookie = logins.validate_cookie(request.cookies.get('jam_login'))
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.PAYMENT_BY_ID, cookie.user.user_id)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.PAYMENT_BY, f"{cookie.user.first_name} {cookie.user.surname}")
    return redirect(url_for("trustee_routes.ledger"))


@trustee_routes.route("/finance/ledger/secondary_approved_by/<transaction_id>")
@trustee_required
@module_finance_required
def ledger_secondary_approved_by_transaction(transaction_id):
    status, cookie = logins.validate_cookie(request.cookies.get('jam_login'))
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.SECONDARY_APPROVED_ID, cookie.user.user_id)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.SECONDARY_APPROVED, f"{cookie.user.first_name} {cookie.user.surname}")
    return redirect(url_for("trustee_routes.ledger"))


@trustee_routes.route("/finance/ledger/verified_by/<transaction_id>")
@trustee_required
@module_finance_required
def ledger_verified_by_transaction(transaction_id):
    status, cookie = logins.validate_cookie(request.cookies.get('jam_login'))
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.VERIFIED_BY_ID, cookie.user.user_id)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.VERIFIED_BY, f"{cookie.user.first_name} {cookie.user.surname}")
    return redirect(url_for("trustee_routes.ledger"))


@trustee_routes.route("/finance/expenses_list")
@trustee_required
@module_finance_required
def expenses_list():
    expenses = google_sheets.get_volunteer_expenses_table()
    user = logins.get_current_user()
    for expense in expenses:
        expense.user_id = user.user_id
    return render_template("trustee/expenses_list.html", expenses=expenses)


@trustee_routes.route("/finance/expenses_list/approved_by/<expense_id>")
@trustee_required
@module_finance_required
def expenses_list_approved_by(expense_id):
    current_user = logins.get_current_user()
    id_column_data = google_sheets.update_expense_cell(expense_id, google_sheets.E.APPROVED_BY_ID, current_user.user_id)
    google_sheets.update_expense_cell(expense_id, google_sheets.E.APPROVED_BY, f"{current_user.first_name} {current_user.surname}", id_column_data=id_column_data)
    return redirect(url_for("trustee_routes.expenses_list"))


@trustee_routes.route("/finance/expenses_list/secondary_approved_by/<expense_id>")
@trustee_required
@module_finance_required
def expenses_list_secondary_approved_by(expense_id):
    current_user = logins.get_current_user()
    id_column_data = google_sheets.update_expense_cell(expense_id, google_sheets.E.SECONDARY_APPROVED_BY_ID, current_user.user_id)
    google_sheets.update_expense_cell(expense_id, google_sheets.E.SECONDARY_APPROVED_BY, f"{current_user.first_name} {current_user.surname}", id_column_data=id_column_data)
    return redirect(url_for("trustee_routes.expenses_list"))


@trustee_routes.route("/finance/expenses_list/paid_by/<expense_id>")
@trustee_required
@module_finance_required
def expenses_list_paid_by(expense_id):
    current_user = logins.get_current_user()
    id_column_data = google_sheets.update_expense_cell(expense_id, google_sheets.E.PAID_BY_ID, current_user.user_id)
    google_sheets.update_expense_cell(expense_id, google_sheets.E.PAID_BY, f"{current_user.first_name} {current_user.surname}", id_column_data=id_column_data)
    google_sheets.update_expense_cell(expense_id, google_sheets.E.PAYMENT_DATE, datetime.today().strftime("%d/%m/%Y"), id_column_data=id_column_data)
    return redirect(url_for("trustee_routes.expenses_list"))


@trustee_routes.route("/finance/ledger_upload_link/<transaction_id>", methods=['GET', 'POST'])
@trustee_required
@module_finance_required
def ledger_upload_link(transaction_id):
    form = forms.AddTransactionReceiptForm(CombinedMultiDict((request.files, request.form)))

    users = database.get_users(include_inactive=True)
    transactions = google_sheets.get_transaction_table(users)
    for transaction in transactions:
        if int(transaction.transaction_id) == int(transaction_id):
            t = transaction
            break
    else:
        return "Transaction not found..."   


    if request.method == 'POST' and form.validate():
        f = form.receipt.data
        month_year = form.receipt_date.data.strftime("%B-%Y").lower()
        file_type = f.filename.split(".")[-1]
        file_uuid = str(uuid.uuid4())[0:8]
        filename = f"{file_uuid}.{file_type}"
        base_dir = f"static/files/receipts/{month_year}"
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        file_path = f"{base_dir}/{filename}"
        if not os.path.isfile(file_path):
            f.save(file_path)
            flash("File upload successful.", "success")
            id_column_data = google_sheets.update_transaction_cell(transaction_id, google_sheets.T.RECEIPT_DATE, form.receipt_date.data.strftime("%d/%m/%Y"))
            google_sheets.update_transaction_cell(transaction_id, google_sheets.T.RECEIPT_URL, f"/{file_path}", id_column_data=id_column_data)
        else:
            flash("Failed to upload - File of same name already exists.", "danger")
        return redirect(url_for("trustee_routes.ledger"))


    nearby_expenses = []
    if "PAYPAL" in t.bank_text:
        expenses = google_sheets.get_volunteer_expenses_table()
        nearby_expenses = []
        for expense in expenses:
            if not expense.payment_made_date:
                continue

            if abs((t.bank_date - expense.payment_made_date).days) < 3 and transaction.paid_out == expense.value and expense.paid_by_id:
                nearby_expenses.append(expense)

    return render_template("trustee/ledger_upload_link.html", transaction=t, expenses=nearby_expenses, form=form)


@trustee_routes.route("/finance/ledger_upload_link/<transaction_id>/link/<expense_id>", methods=['GET', 'POST'])
@trustee_required
@module_finance_required
def ledger_upload_link_expense(transaction_id, expense_id):
    expenses = google_sheets.get_volunteer_expenses_table()
    
    for expense in expenses:
        if int(expense.expense_id) == int(expense_id):
            expense_object = expense
            break
    else:
        return "Unable to find expense"
    
    id_column_data = google_sheets.update_transaction_cell(transaction_id, google_sheets.T.RECEIPT_DATE, expense.receipt_date.strftime("%d/%m/%Y"))
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.RECEIPT_URL, expense.receipt_url, id_column_data=id_column_data)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.SUPPLIER, "Volunteer Expense", id_column_data=id_column_data)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.DESCRIPTION, f"Expense ID - {expense.expense_id}", id_column_data=id_column_data)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.PAYMENT_BY_ID, expense.volunteer_id, id_column_data=id_column_data)
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.PAYMENT_BY, expense.volunteer_name, id_column_data=id_column_data)
    flash("Transactions successfully linked", "success")
    return redirect(url_for("trustee_routes.ledger"))



@trustee_routes.route("/static/files/receipts/<folder>/<filename>")
@trustee_required
@module_finance_required
def files_download(folder, filename):
    return send_file(f"static/files/receipts/{folder}/{filename}")



# -------------- AJAX routes -------------


@trustee_routes.route("/finance/ledger/update_description_ajax", methods=['GET', 'POST'])
@trustee_required
@module_finance_required
def ledger_update_description():
    transaction_id = request.form['transaction_id']
    description = request.form['description']
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.DESCRIPTION, description)
    return ""


@trustee_routes.route("/finance/ledger/update_supplier_ajax", methods=['GET', 'POST'])
@trustee_required
@module_finance_required
def ledger_update_supplier():
    transaction_id = request.form['transaction_id']
    supplier = request.form['supplier']
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.SUPPLIER, supplier)
    return ""


@trustee_routes.route("/finance/ledger/update_notes_ajax", methods=['GET', 'POST'])
@trustee_required
@module_finance_required
def ledger_update_notes():
    transaction_id = request.form['transaction_id']
    notes = request.form['notes']
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.NOTES, notes)
    return ""


@trustee_routes.route("/finance/ledger/update_category_ajax", methods=['GET', 'POST'])
@trustee_required
@module_finance_required
def ledger_update_category():
    transaction_id = request.form['transaction_id']
    notes = request.form['category']
    google_sheets.update_transaction_cell(transaction_id, google_sheets.T.CATEGORY, notes)
    return ""


@trustee_routes.route("/finance/expenses_list/rejection_reason", methods=['GET', 'POST'])
@trustee_required
@module_finance_required
def expenses_list_rejection_reason():
    expense_id = request.form['expense_id']
    rejection_reason = request.form['rejection_reason']
    google_sheets.update_expense_cell(expense_id, google_sheets.E.REJECTION_REASON, rejection_reason)
    return ""