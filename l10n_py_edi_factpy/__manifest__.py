{
    "name": "Paraguay - FactPy EDI Connector",
    "version": "17.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "summary": "FactPy connector for Electronic Invoicing in Paraguay",
    "description": """
FactPy EDI Connector for Paraguay
=================================

This module provides integration with FactPy service for electronic invoicing
in Paraguay, compliant with SET (Subsecretaría de Estado de Tributación) requirements.

Features:
---------
* Integration with FactPy API
* Document sending and status checking
* Document cancellation
* PDF and XML download
* Automatic error handling and logging

Requirements:
-------------
* l10n_py_edi_base module must be installed
* FactPy account credentials (API Key and Secret)

Configuration:
--------------
1. Go to Settings > Technical > System Parameters
2. Set l10n_py.edi_provider = 'factpy'
3. Configure connector in Facturación Electrónica > Connectors
    """,
    "author": "KMEE",
    "website": "https://github.com/OCA/l10n-paraguay",
    "license": "LGPL-3",
    "depends": [
        "l10n_py_edi_base",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/factpy_connector_views.xml",
        # Wizard
        "wizard/factpy_connector_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
