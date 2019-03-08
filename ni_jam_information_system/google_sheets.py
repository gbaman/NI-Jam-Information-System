import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import database
from secrets.config import finance_google_sheet_id


scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('secrets/client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(finance_google_sheet_id)


class Transaction():
    def __init__(self, raw_row, offset=1, bank=False):
        row = raw_row[offset:]
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
        
        self.offset = offset
        self.editing = False

    @property
    def paid_out_symbol(self):
        if self.paid_out:
            return f"£{self.paid_out}"
        return ""

    @property
    def paid_in_symbol(self):
        if self.paid_in:
            return f"£{self.paid_in}"
        return ""
    
    def update_trustees(self, trustees):
        for trustee in trustees:
            if self.payment_by_id and int(self.payment_by_id) == int(trustee.user_id):
                self.payment_by = f"{trustee.first_name} {trustee.surname}"
            
            if self.secondary_approved_by_id and int(self.secondary_approved_by_id) == int(trustee.user_id):
                self.secondary_approved_by = f"{trustee.first_name} {trustee.surname}"
                
            if self.verified_by_id and int(self.verified_by_id) == int(trustee.user_id):
                self.verified_by = f"{trustee.first_name} {trustee.surname}"
    
    
    def get_row(self):
        offset = []
        for i in range(0, self.offset):
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


def import_bank_csv(csv_path):
    import csv
    
    transactions = []
    with open(csv_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for line in list(csv_reader)[1:]:
            transactions.append(Transaction((None, line[0], None, None, line[2], None, None, line[3], line[4], None, None, None, None, None, None, None, None, None),offset=0, bank=True))
    current_transactions = get_transaction_table()
    new_transactions = []
    for new_transaction in transactions:
        duplicate = False
        for current_transaction in current_transactions:
            if new_transaction.bank_date == current_transaction.bank_date:
                if new_transaction.bank_text.strip() == current_transaction.bank_text.strip():
                    if new_transaction.paid_in == current_transaction.paid_in and new_transaction.paid_out == current_transaction.paid_out:
                        #print("Duplicate found... {}".format(new_transaction))
                        duplicate = True
                        break
                    else:
                        print("Money doesn't match for a transaction {} - {} vs {}".format(new_transaction.bank_text, new_transaction.paid_out, current_transaction.paid_out))
                        #raise Exception ("Money doesn't match for a transaction {} - {} vs {}".format(new_transaction.bank_text, new_transaction.paid_out, current_transaction.paid_out))
        if duplicate:
            continue
        new_transactions.append(new_transaction)
    worksheet = sheet.worksheet("Main")
    transaction_id = current_transactions[-1].transaction_id
    for new_transaction in new_transactions:
        transaction_id = int(transaction_id) + 1
        new_transaction.transaction_id = transaction_id
        worksheet.append_row(new_transaction.get_row(), value_input_option='USER_ENTERED')


def get_transaction_table(offset=3):
    trustees = database.get_all_trustees()
    transaction_data = []
    worksheet = sheet.worksheet("Main")
    data = worksheet.get_all_values()[offset:]
    for line in data:
        t = Transaction(line)
        t.update_trustees(trustees)
        transaction_data.append(t)

    return transaction_data


def get_volunteer_expenses_table(offset=3):
    expense_data = []
    worksheet = sheet.worksheet("Volunteer expenses")
    data = worksheet.get_all_values()[offset:]
    for line in data:
        expense_data.append(Expense(line))

    return expense_data


#get_volunteer_expenses_table()
#get_transaction_table()
#import_bank_csv("transactions.csv",)
