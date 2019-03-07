import gspread
from oauth2client.service_account import ServiceAccountCredentials
from secrets.config import finance_google_sheet_id


scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('secrets/client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(finance_google_sheet_id)


class Transaction():
    transaction_id = None
    bank_date = None
    receipt_date = None
    supplier = None
    bank_text = None
    description = None
    receipt_url = None
    paid_out = None
    paid_in = None
    payment_by_id = None
    payment_by = None
    secondary_approved_by_id = None
    secondary_approved_by = None
    verified_by_id = None
    verified_by = None
    category = None
    treasurer_notes = None

    def __init__(self, raw_row, offset=1):
        row = raw_row[offset:]
        self.transaction_id = row[0]
        self.bank_date = row[1]
        self.receipt_date = row[2]
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
        print()


class Expense():
    def __init__(self, raw_row, offset=1):
        row = raw_row[offset:]
        self.receipt_date = row[0]
        self.volunteer_id = row[1]
        self.volunteer_name = row[2]
        self.paypal_email = row[3]
        self.receipt_url = row[4]
        self.value = row[5]
        self.approved_by_id = row[6]
        self.approved_by = row[7]
        self.secondary_approved_by_id = row[8]
        self.secondary_approved_by = row[9]
        self.status = row[10]
        self.rejected_reason = row[11]
        print()


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
