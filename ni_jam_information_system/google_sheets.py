import datetime
import threading
import time

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import database
import models
from secrets.config import finance_google_sheet_id

scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('secrets/client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(finance_google_sheet_id)
a = time.time()
MAIN_SHEET = None
EXPENSE_SHEET = None
CATEGORIES_SHEET = None

BANK_TEXT_AUTO_FILL = {
    "GSUITE_nir CC@GOOGLE.COM": "Google",
    "RS COMPONENTS": "RS Components",
    "LITTLE WING": "Little Wings",
    "TESCO STORES": "Tescos",
    "Amazon.co.uk": "Amazon",
    "AMZ*": "Amazon",
    "HSBC": "HSBC"
}


# Used to allow main Flask app to start for development, without waiting ~2 seconds extra for sheets to be setup.
def setup_worksheets_in_background():
    global MAIN_SHEET, EXPENSE_SHEET, CATEGORIES_SHEET
    MAIN_SHEET = sheet.worksheet("Main")
    EXPENSE_SHEET = sheet.worksheet("Volunteer expenses")
    CATEGORIES_SHEET = sheet.worksheet("Categories")
    print("Finance worksheets setup")


thread = threading.Thread(target=setup_worksheets_in_background)
thread.start()


class T():
    RECEIPT_DATE = 4
    SUPPLIER = 5
    DESCRIPTION = 7
    RECEIPT_URL = 8
    PAID_OUT = 9
    PAYMENT_BY_ID = 11
    PAYMENT_BY = 12
    SECONDARY_APPROVED_ID = 13
    SECONDARY_APPROVED = 14
    VERIFIED_BY_ID = 15
    VERIFIED_BY = 16
    CATEGORY = 17
    NOTES = 18
    EXPENSE_ID = 19


class E():
    APPROVED_BY_ID = 10
    APPROVED_BY = 11
    SECONDARY_APPROVED_BY_ID = 12
    SECONDARY_APPROVED_BY = 13
    PAID_BY_ID = 14
    PAID_BY = 15
    REJECTION_REASON = 16
    PAYMENT_DATE = 17
    EXPENSE_TYPE = 18


class Transaction():
    user_id = None

    def __init__(self, raw_row=None, offset=1, bank=False):
        if not raw_row:
            row = [-1, "01/01/2000", "01/01/2000", "ERROR", "ERROR", "ERROR", "", "-1", "-1", None, None, None, None, None, None, "ERROR", "ERROR", None]
            self.error = True
        else:
            row = raw_row[offset:]
            self.error = False
        self.transaction_id = row[0]
        self.bank_date = _convert_date(row[1], bank)
        self.receipt_date = _convert_date(row[2], bank)
        self.supplier = row[3]
        self.bank_text = row[4]
        self.description = row[5]
        self.receipt_url = row[6]
        self.paid_out = _clean_money_value(row[7])
        self.paid_in = _clean_money_value(row[8])
        self.payment_by_id = row[9]
        self.payment_by = row[10]
        self.secondary_approved_by_id = row[11]
        self.secondary_approved_by = row[12]
        self.verified_by_id = row[13]
        self.verified_by = row[14]
        self.category = row[15]
        self.treasurer_notes = row[16]
        self.expense_id = row[17]

        self.offset = offset
        self.editing = False

    @property
    def paid_out_symbol(self):
        if self.paid_out:
            return f"-£{self.paid_out}"
        return ""

    @property
    def paid_in_symbol(self):
        if self.paid_in:
            return f"+£{self.paid_in}"
        return ""

    @property
    def button_disabled(self):
        self.user_id = int(self.user_id)
        if (self.payment_by_id and int(self.payment_by_id) == int(self.user_id)) \
                or (self.verified_by_id and int(self.verified_by_id) == self.user_id) \
                or (self.secondary_approved_by_id and int(self.secondary_approved_by_id) == self.user_id):
            return 'disabled'
        return ""

    @property
    def verified_by_button_disabled(self):
        if self.button_disabled == "disabled" or not self.receipt_url:
            return "disabled"
        return ""

    @property
    def supplier_colour(self):
        if not self.supplier or self.error:
            return "#ff928a"
        return "#ffffff"

    @property
    def description_colour(self):
        if not self.description or self.error:
            return "#ff928a"
        return "#ffffff"

    @property
    def category_colour(self):
        if not self.category or self.error:
            return "#ff928a"
        return "#ffffff"

    def update_names(self, trustees):
        for trustee in trustees:
            if self.payment_by_id and int(self.payment_by_id) == int(trustee.user_id):
                self.payment_by = f"{trustee.first_name} {trustee.surname}"

            if self.secondary_approved_by_id and int(self.secondary_approved_by_id) == int(trustee.user_id):
                self.secondary_approved_by = f"{trustee.first_name} {trustee.surname}"

            if self.verified_by_id and int(self.verified_by_id) == int(trustee.user_id):
                self.verified_by = f"{trustee.first_name} {trustee.surname}"

    def get_row(self):
        offset = []
        for i in range(0, self.offset+1):
            offset.append("")
        if self.bank_date:
            bank_date = self.bank_date.strftime("%d/%m/%Y")
        else:
            bank_date = None

        if self.receipt_date:
            receipt_date = self.receipt_date.strftime("%d/%m/%Y")
        else:
            receipt_date = None

        return offset + [self.transaction_id, bank_date, receipt_date, self.supplier, self.bank_text, self.description,
                         self.receipt_url, self.paid_out, self.paid_in, self.payment_by_id, self.payment_by, self.secondary_approved_by_id,
                         self.secondary_approved_by, self.verified_by_id, self.verified_by, self.category, self.treasurer_notes]


class Expense():
    user_id = None

    def __init__(self, raw_row, offset=1):
        row = raw_row[offset:]
        self.expense_id = row[0]
        self.expense_submit_date = datetime.datetime.strptime(row[1], "%d/%m/%Y").date()
        self.receipt_date = datetime.datetime.strptime(row[2], "%d/%m/%Y").date()
        self.volunteer_id = row[3]
        self.volunteer_name = row[4]
        self.volunteer_object: models.LoginUser = models.LoginUser()
        self.paypal_email = row[5]
        self.receipt_url = row[6]
        self.value = row[7]
        self.approved_by_id = row[8]
        self.approved_by = row[9]
        self.approved_by_object: models.LoginUser = models.LoginUser()
        self.secondary_approved_by_id = row[10]
        self.secondary_approved_by = row[11]
        self.secondary_approved_by_object: models.LoginUser = models.LoginUser()
        self.paid_by_id = row[12]
        self.paid_by = row[13]
        self.paid_by_object: models.LoginUser = models.LoginUser()
        self.rejected_reason = row[14]
        self.payment_made_date = None
        self.expense_type = row[16]

        if row[15]:
            self.payment_made_date = datetime.datetime.strptime(row[15], "%d/%m/%Y").date()

    @property
    def value_symbol(self):
        if self.value:
            return f"£{self.value}"
        return ""

    @property
    def button_disabled(self):
        self.user_id = int(self.user_id)
        if (self.approved_by_id and int(self.approved_by_id) == int(self.user_id)) or (self.secondary_approved_by_id and int(self.secondary_approved_by_id) == self.user_id) or (self.volunteer_id and int(self.volunteer_id) == self.user_id):
            return 'disabled'
        return ""

    @property
    def paid_button_disabled(self):
        self.user_id = int(self.user_id)
        if self.approved_by_id and self.secondary_approved_by_id:
            return ""
        return "disabled"

    @property
    def status(self):
        if self.rejected_reason:
            return f"Rejected : {self.rejected_reason}"
        elif self.paid_by_id:
            return f"Payment made on {self.payment_made_date}"
        elif self.secondary_approved_by_id:
            return "Approved - Awaiting payment"
        elif self.approved_by_id:
            return "1/2 approvals complete"
        else:
            return "Awaiting approvals"

    @property
    def status_colour(self):
        if self.rejected_reason:
            return "#ff9e9e"
        elif self.paid_by_id:
            return "#9effbb"
        else:
            return ""

    def update_users(self, login_users):
        for user in login_users:
            if self.volunteer_id and int(self.volunteer_id) == user.user_id:
                self.volunteer_name = f"{user.first_name} {user.surname}"
                self.volunteer_object = user

            if self.approved_by_id and int(self.approved_by_id) == user.user_id:
                self.approved_by = f"{user.first_name} {user.surname}"
                self.approved_by_object = user

            if self.secondary_approved_by_id and int(self.secondary_approved_by_id) == user.user_id:
                self.secondary_approved_by = f"{user.first_name} {user.surname}"
                self.secondary_approved_by_object = user

            if self.paid_by_id and int(self.paid_by_id) == user.user_id:
                self.paid_by = f"{user.first_name} {user.surname}"
                self.paid_by_object = user


def _convert_date(date_string, bank):
    if date_string:
        if bank:
            return datetime.datetime.strptime(date_string, "%d %b %Y").date()
        else:
            return datetime.datetime.strptime(date_string, "%d/%m/%Y").date()
    return None


def _clean_money_value(value):
    if value and value.strip():
        value = value.strip()
        if value[0] == "£":
            return value[1:]
        elif not "." in value:
            return "{}.00".format(value)
        else:
            return value
    return None


def _check_oauth_token():
    if creds.access_token_expired:
        client.login()


def import_bank_csv(csv_path):
    import csv

    transactions = []
    _check_oauth_token()
    with open(csv_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for line in list(csv_reader)[1:]:
            transactions.append(Transaction((None, line[0], None, None, line[2], None, None, line[3], line[4], None, None, None, None, None, None, None, None, None, None), offset=0, bank=True))
    logins = database.get_users(include_inactive=True)
    current_transactions = get_transaction_table(logins)
    new_transactions = []
    for new_transaction in transactions:
        duplicate = False
        for current_transaction in current_transactions:
            if new_transaction.bank_date == current_transaction.bank_date:
                if new_transaction.bank_text.strip() == current_transaction.bank_text.strip():
                    if new_transaction.paid_in == current_transaction.paid_in and new_transaction.paid_out == current_transaction.paid_out:
                        # print("Duplicate found... {}".format(new_transaction))
                        duplicate = True
                        break
                    else:
                        print("Money doesn't match for a transaction {} - {} vs {}".format(new_transaction.bank_text, new_transaction.paid_out, current_transaction.paid_out))
                        # raise Exception ("Money doesn't match for a transaction {} - {} vs {}".format(new_transaction.bank_text, new_transaction.paid_out, current_transaction.paid_out))
        if duplicate:
            continue
        new_transactions.append(new_transaction)
    transaction_id = current_transactions[-1].transaction_id
    for new_transaction in new_transactions:
        transaction_id = int(transaction_id) + 1
        new_transaction.transaction_id = transaction_id
        auto_fill_expense_data(new_transaction)
        MAIN_SHEET.append_row(new_transaction.get_row(), value_input_option='USER_ENTERED')


def get_all_values_for_table(table, return_data):
    return_data.append(table.get_all_values())
    return return_data


def get_table_data_from_sheets(main_transactions=True, volunteer_expenses=True, categories=True):
    main_sheet_data = []
    if main_transactions:
        main_sheet_data_thread = threading.Thread(target=get_all_values_for_table, args=(MAIN_SHEET, main_sheet_data))
    expenses_sheet_data = []
    if volunteer_expenses:
        expenses_sheet_data_thread = threading.Thread(target=get_all_values_for_table, args=(EXPENSE_SHEET, expenses_sheet_data))
    categories_data = []
    if categories:
        categories_data_thread = threading.Thread(target=get_all_values_for_table, args=(CATEGORIES_SHEET, categories_data))

    if main_transactions:
        main_sheet_data_thread.start()
    if volunteer_expenses:
        expenses_sheet_data_thread.start()
    if categories:
        categories_data_thread.start()

    if main_transactions:
        main_sheet_data_thread.join()
        main_sheet_data = main_sheet_data[0]
    if volunteer_expenses:
        expenses_sheet_data_thread.join()
        expenses_sheet_data = expenses_sheet_data[0]
    if categories:
        categories_data_thread.join()
        categories_data = categories_data[0]

    return main_sheet_data, expenses_sheet_data, categories_data


def get_transaction_table(logins, offset=3, main_sheet_data=None, categories_data=None):
    _check_oauth_token()
    transaction_data = []

    if not main_sheet_data or not categories_data:
        main_sheet_data, volunteer_expenses, categories_data = get_table_data_from_sheets(main_transactions=True, volunteer_expenses=False, categories=True)

    main_sheet_data = main_sheet_data[offset:]
    categories_data = categories_data[2:]
    categories = []
    for line in categories_data:
        if line[1]:
            categories.append(line[1])
    for line_id, line in enumerate(main_sheet_data):
        try:
            if line[0] == "#HEADING":
                continue # Ignore any row with #HEADING in the 1st column
            t = Transaction(line)
            t.categories = categories
            t.update_names(logins)
            transaction_data.append(t)
        except ValueError:
            print(f"Unable in load value at row {line_id}!")
            transaction_data.append(Transaction())
    return transaction_data


def get_volunteer_expenses_table(offset=3, volunteer_expenses=None):
    expense_data = []
    _check_oauth_token()
    if not volunteer_expenses:
        main_transactions, volunteer_expenses, categories = get_table_data_from_sheets(main_transactions=False, volunteer_expenses=True, categories=False)
    volunteer_expenses = volunteer_expenses[offset:]
    login_users = database.get_users(include_inactive=True)
    for line in volunteer_expenses:
        expense = Expense(line)
        expense.update_users(login_users)
        expense_data.append(expense)

    return expense_data


def update_transaction_cell(transaction_id, cell_id, new_string, id_column_data=None):
    _check_oauth_token()
    if not id_column_data:
        id_column_data = MAIN_SHEET.range("B4:B{}".format(MAIN_SHEET.row_count))
    for cell in id_column_data:
        if cell.value == str(transaction_id):
            transaction_row_id = cell.row
            break
    else:
        print("Unable to find transaction with ID {}".format(transaction_id))
        return None
    MAIN_SHEET.update_cell(transaction_row_id, cell_id, new_string)
    return id_column_data


def update_expense_cell(expense_id, cell_id, new_string, id_column_data=None):
    _check_oauth_token()
    if not id_column_data:
        id_column_data = EXPENSE_SHEET.range("B4:B{}".format(EXPENSE_SHEET.row_count))
    for cell in id_column_data:
        if cell.value == str(expense_id):
            expense_row_id = cell.row
            break
    else:
        print("Unable to find expense with ID {}".format(expense_id))
        return None
    EXPENSE_SHEET.update_cell(expense_row_id, cell_id, new_string)
    return id_column_data


def create_expense_row(e: Expense):
    _check_oauth_token()
    expenses = get_volunteer_expenses_table()
    if expenses:
        e.expense_id = int(expenses[-1].expense_id) + 1
    else:
        e.expense_id = 0
    EXPENSE_SHEET.append_row([e.expense_id, e.expense_submit_date.strftime("%d/%m/%Y"), e.receipt_date.strftime("%d/%m/%Y"), e.volunteer_id, e.volunteer_name, e.paypal_email, e.receipt_url, e.value, None, None, None, None, None, None, None, None, e.expense_type], value_input_option='USER_ENTERED')


def auto_fill_expense_data(transaction):
    # Guess supplier from bank_text
    for text in BANK_TEXT_AUTO_FILL:
        if text.lower() in transaction.bank_text.lower():
            transaction.supplier = BANK_TEXT_AUTO_FILL[text]
