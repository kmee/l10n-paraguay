{
    "name": "Paraguay - Accounting",
    "version": "17.0.1.0.0",
    "category": "Accounting/Localizations/Account Charts",
    "summary": "Localización contable para Paraguay",
    "description": """
Paraguay Chart of Accounts
==========================

This module provides the Paraguayan chart of accounts and tax configuration:

* Standard chart of accounts for Paraguay
* Tax configuration (IVA 10%, IVA 5%, Exempt)
* Tax groups and fiscal positions

This is the base accounting module. For additional features, install:
- l10n_py_account: Accounting extensions (journals, authorizations)
- l10n_py_edi_base: Electronic invoicing base functionality
    """,
    "author": "KMEE",
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
        "data/account_tax_group_data.xml",
        "data/account_chart_template_data.xml",
        # Views
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
