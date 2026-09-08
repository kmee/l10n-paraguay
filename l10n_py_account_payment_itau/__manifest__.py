{
    "name": "Paraguay - Banco Itaú Open Banking Payment Integration Base",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations",
    "summary": "mTLS-authenticated REST client and credential storage "
    "for Banco Itaú Paraguay (IOB - Itaú Open Banking)",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-paraguay",
    "license": "LGPL-3",
    "depends": [
        "l10n_py_base",
        "base_iban",
    ],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "views/res_partner_bank_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
