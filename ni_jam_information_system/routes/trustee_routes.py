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
    form = forms.LedgerEditForm(request.form)
    transactions = google_sheets.get_transaction_table()
    
    if request.method == 'POST' and form.validate():
        transaction = None
        for t in transactions:
            if int(t.transaction_id) == int(transaction_id):
                transaction = t
                break
        transaction.editing = True
       # form.payment_by.
        
    transactions[0].editing = True
    trustees = database.get_all_trustees()
    return render_template("trustee/ledger.html", transactions=transactions, trustees=trustees, form=form)



# -------------- AJAX routes -------------

@trustee_routes.route("/finance/ledger/update_description_ajax", methods=['GET', 'POST'])
@trustee_required
def ledger_update_description():
    transaction_id = request.form['transaction_id']
    description = request.form['description']
    a = google_sheets.update_transaction_cell(transaction_id, google_sheets.T.DESCRIPTION, description)
    return ""