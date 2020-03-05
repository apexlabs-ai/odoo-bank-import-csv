import logging
import io
import csv
import hashlib

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


FIELDNAMES = [
    'Accountnummer',
    'Kaartnummer',
    'Naam op kaart',
    'Transactiedatum',
    'Boekingsdatum',
    'Omschrijving',
    'Valuta',
    'Bedrag',
    'Koers',
    'Bedrag in EUR'
]


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _prepare_transaction_line(self, row):
        vals = {
            'date': row["Boekingsdatum"],
            'name': row["Omschrijving"],
            'amount': float(row["Bedrag in EUR"].replace(',', '.')),
        }
        vals['ref'] = vals['unique_import_id'] = hashlib.md5(
            str(vals).encode('utf-8')).hexdigest()
        if row['Valuta']:
            vals['name'] += (
                ' // ' + row['Valuta'] + row['Bedrag']
                + '@' + row['Koers'])

        return vals

    def _parse_file(self, data_file):
        reader = csv.DictReader(io.StringIO(data_file.decode('utf-8')))

        if reader.fieldnames != FIELDNAMES:
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

        transactions = []
        total_amt = 0.00
        account = None

        try:
            for row in reader:
                if not account:
                    account = row["Accountnummer"]
                elif account != row["Accountnummer"]:
                    raise UserError(_(
                        "Multi-account statements are not supported. "))
                vals = self._prepare_transaction_line(row)
                if vals:
                    transactions.append(vals)
                    total_amt += vals['amount']
        except Exception as e:
            raise UserError(_(
                "The following problem occurred during import. "
                "The file might not be valid.\n\n %s") % e.message)

        # balance = float(ofx.account.statement.balance)
        vals_bank_statement = {
            'name': account,
            'transactions': transactions,
            'balance_start': 0,
            'balance_end_real': total_amt,
        }
        return "EUR", account, [vals_bank_statement]
