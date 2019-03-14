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
@trustee_routes.route("/finance/ledger/<transaction_id>", methods=['GET', 'POST'])
@trustee_required
def ledger(transaction_id=None):
    transactions = google_sheets.get_transaction_table()
    trustees = database.get_all_trustees()
    return render_template("trustee/ledger.html", transactions=transactions, trustees=trustees)



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