{
    "name": "Paraguay - Accounting Extensions",
    "version": "16.0.1.0.0",
    "category": "Accounting/Localizations",
    "summary": "Accounting extensions for Paraguay localization",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-paraguay",
    "license": "LGPL-3",
    "depends": [
        "account",
        "l10n_py_base",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Data
        "data/account_authorization_sequence.xml",
        # Views
        "views/account_authorization_views.xml",
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
    ],
    "demo": [
        "demo/account_authorization_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
