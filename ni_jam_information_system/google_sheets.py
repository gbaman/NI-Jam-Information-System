import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from secrets.config import finance_google_sheet_id


scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('secrets/client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(finance_google_sheet_id)


class Transaction():
    def __init__(self, raw_row, offset=1):
        row = raw_row[offset:]
        self.transaction_id = row[0]
        self.bank_date = datetime.datetime.strptime(row[1], "%d/%m/%Y").date()
        self.receipt_date = datetime.datetime.strptime(row[2], "%d/%m/%Y").date()
        self.supplier = row[3]
        self.bank_text = row[4]
        self.description = row[5]
        self.receipt_url = row[6]
        self.paid_out = row[7]
        self.paid_in = row[8]
        self.payment_by_id = row[9]
        self.payment_by = row[10]
        self.secondary_approved_by_id = row[11]
        self.secondary_approved_by = row[12]
        self.verified_by_id = row[13]
        self.verified_by = row[14]
        self.category = row[15]
        self.treasurer_notes = [16]


class Expense():
    def __init__(self, raw_row, offset=1):
        row = raw_row[offset:]
        self.expense_id = row[0]
        self.expense_submit_date = datetime.datetime.strptime(row[1], "%d/%m/%Y").date()
        self.receipt_date = datetime.datetime.strptime(row[2], "%d/%m/%Y").date()
        self.volunteer_id = row[3]
        self.volunteer_name = row[4]
        self.paypal_email = row[5]
        self.receipt_url = row[6]
        self.value = row[7]
        self.approved_by_id = row[8]
        self.approved_by = row[9]
        self.secondary_approved_by_id = row[10]
        self.secondary_approved_by = row[11]
        self.status = row[12]
        self.rejected_reason = row[13]


def get_transaction_table(offset=3):
    transaction_data = []
    worksheet = sheet.worksheet("Main")
    data = worksheet.get_all_values()[offset:]
    for line in data:
        transaction_data.append(Transaction(line))

    return transaction_data


def get_volunteer_expenses_table(offset=3):
    expense_data = []
    worksheet = sheet.worksheet("Volunteer expenses")
    data = worksheet.get_all_values()[offset:]
    for line in data:
        expense_data.append(Expense(line))

    return expense_data


get_volunteer_expenses_table()
get_transaction_table()
