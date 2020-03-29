import logging
import io
import csv
import hashlib

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


FIELDNAMES = [
    'Date started',
    'Time started',
    'Date completed',
    'Time completed',
    'State',
    'Type',
    'Description',
    'Reference',
    'Payer',
    'Card name',
    'Card number',
    'Orig currency',
    'Orig amount',
    'Payment currency',
    'Amount',
    'Fee',
    'Balance',
    'Account',
    'Beneficiary account number',
    'Beneficiary sort code or routing number',
    'Beneficiary IBAN',
    'Beneficiary BIC'
]


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _prepare_transaction_line_revolut(self, row):
        vals = {
            'date': row["Date completed"],
            'name': row["Description"].replace('To ', '').replace('From ',''),
            'amount': float(row["Amount"]),
            'account_number': row["Beneficiary account number"] or row["Beneficiary IBAN"],
            'note': row["Reference"]
        }

        if row["Card name"]:
            vals['name'] += " / {}".format(row["Card name"])

        if row["Payment currency"] != row["Orig currency"]:
            vals['name'] += "  ({} {})".format(row["Orig currency"], row["Orig amount"])

        if row["Fee"]:
            fee = float(row["Fee"])
            if fee:
                vals['amount'] += fee
                vals['name'] += "  Fee: {}".format(row["Fee"])

        vals['ref'] = vals['unique_import_id'] = hashlib.md5(
            str(vals).encode('utf-8')).hexdigest()

        return vals, float(row["Balance"])

    def _parse_file(self, data_file):
        reader = csv.DictReader(io.StringIO(data_file.decode('utf-8-sig')))

        if reader.fieldnames != FIELDNAMES:
            return super()._parse_file(data_file)

        transactions = []
        total_amt = 0.00
        account = None
        currency = None
        balance_end = None
        balance_start = None

        try:
            for row in reader:
                if not currency:
                    currency = row["Payment currency"]
                elif currency != row["Payment currency"]:
                    raise UserError(_(
                        "Multi-currency statements are not supported. "))
                if not account:
                    account = row["Account"]
                elif account != row["Account"]:
                    raise UserError(_(
                        "Multi-account statements are not supported. "))
                vals, balance = self._prepare_transaction_line_revolut(row)

                if vals:
                    transactions.append(vals)
                    total_amt += vals['amount']
                if balance:
                    if balance_end is None:
                        balance_end = balance
                    balance_start = balance - vals['amount']

        except Exception as e:
            raise UserError(_(
                "The following problem occurred during import. "
                "The file might not be valid.\n\n %s") % e.message)


        vals_bank_statement = {
            'name': account,
            'transactions': transactions,
            'balance_start': balance_start,
            'balance_end_real': balance_end,
        }
        return currency, account, [vals_bank_statement]
