import logging
import io
import csv
import hashlib

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

FIELDNAMES = [
    "ID of transaction",
    "Date",
    "Volume",
    "Currency",
    "To account",
    "Corresponding account name",
    "Bank Code",
    "Bank Name",
    "KS",
    "VS",
    "SS",
    "Note",
    "Message for beneficiary",
    "Type",
    "Executed",
    "Specification",
    "Note",
    "BIC",
    "ID of payment order"
]

HEADER_FIELDS = [
    ("accountId", str),
    ("bankId", str),
    ("currency", str),
    ("iban", str),
    ("bic", str),
    ("openingBalance", float),
    ("closingBalance", float),
    ("dateStart", str),
    ("dateEnd", str),
    ("idFrom", str),
    ("idTo",  str)
]


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _prepare_transaction_line_fio(self, row):
        if row["Bank Code"]:
            row["To account"] += ("/" + row["Bank Code"])
        vals = {
            'date': row["Date"],
            'name': row["BIC"] or row["To account"],
            'account_number': row["BIC"] or row["To account"],
            'amount': float(row["Volume"]),
            'note': row["Message for beneficiary"],
            'ref': row["ID of transaction"],
            'unique_import_id': row["ID of transaction"]
        }
        if row["Note"]:
            vals['note'] += ("/" + row["Note"])
            
        for symbol in ("KS", "VS", "SS"):
            if row[symbol]:
                vals['note'] += " {}:{}".format(symbol, row[symbol])
                vals['name'] += " {}:{}".format(symbol, row[symbol])
        return vals

    def _parse_file(self, data_file):
        input = io.StringIO(data_file.decode('utf-8-sig'))

        header = self._read_header(input)

        if header is None:
            return super()._parse_file(data_file)

        reader = csv.DictReader(input, delimiter=';')

        if reader.fieldnames != FIELDNAMES:
            raise UserError(_(
                "FIO Bank file, but format is incorrect"))

        transactions = []
        total_amt = 0.00
        account = header['iban']
        currency = header['currency']

        try:
            for row in reader:
                if not currency:
                    currency = row["Currency"]
                elif currency != row["Currency"]:
                    raise UserError(_(
                        "Multi-currency statements are not supported. "))

                vals = self._prepare_transaction_line_fio(row)

                if vals:
                    transactions.append(vals)
                    total_amt += vals['amount']
        except Exception as e:
            raise UserError(_(
                "The following problem occurred during import. "
                "The file might not be valid.\n\n %s") % getattr(e, 'message', e))

        vals_bank_statement = {
            'name': account,
            'transactions': transactions,
            'balance_start': header['openingBalance'],
            'balance_end_real': header['closingBalance'],
        }
        return currency, account, [vals_bank_statement]

    def _read_header(self, input):
        header = {}
        reader = csv.reader(input, delimiter=';')

        try:
            for field in HEADER_FIELDS:
                key, val = next(reader)
                if key != field[0]:
                    return None
                if field[1] == float:
                    val = val.encode('ascii', 'ignore').decode('unicode_escape').replace(',', '.').replace(' ', '')
                    val = float(val)
                header[key] = val

            if next(reader) == []:
                return header

        except (StopIteration, ValueError):
            pass
