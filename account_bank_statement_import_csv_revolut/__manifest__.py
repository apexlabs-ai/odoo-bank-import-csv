{
    'name': 'Import CSV Bank Statement -- Revolut',
    'category': 'Banking addons',
    'version': '12.0.2.0',
    'license': 'AGPL-3',
    'author': 'Alexey Yushin',
    'website': 'https://github.com/apexlabs-ai/odoo-bank-import-csv',
    'depends': [
        'account_bank_statement_import',
    ],
    'data': [
        'views/view_account_bank_statement_import.xml',
    ],
    'installable': True,
}
