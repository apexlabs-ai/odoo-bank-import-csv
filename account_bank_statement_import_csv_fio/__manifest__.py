{
    'name': 'Import FIO Bank (CZ) CSV',
    'category': 'Banking addons',
    'version': '11.0.1.0.0',
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
