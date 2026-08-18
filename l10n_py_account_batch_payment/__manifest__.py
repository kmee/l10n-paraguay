{
    "name": "Paraguay - SIPAP Batch Payment Framework",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations",
    "summary": "Framework to export batch payments for the Paraguayan SIPAP "
    "interbank system (Bancard)",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-paraguay",
    "license": "LGPL-3",
    "depends": [
        "account_batch_payment",
        "l10n_py_base",
    ],
    "data": [
        # Data
        "data/account_payment_method_data.xml",
        # Views
        "views/res_bank_views.xml",
        "views/res_partner_bank_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
