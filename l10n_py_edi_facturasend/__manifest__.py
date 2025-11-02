# -*- coding: utf-8 -*-
{
    'name': 'Paraguay - FacturaSend EDI Connector',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Localizations/EDI',
    'summary': 'FacturaSend connector for Electronic Invoicing in Paraguay',
    'description': """
FacturaSend EDI Connector for Paraguay
======================================

This module provides integration with FacturaSend service for electronic invoicing
in Paraguay, compliant with SET (Subsecretaría de Estado de Tributación) requirements.

Features:
---------
* Integration with FacturaSend API
* Document sending and status checking
* Document cancellation
* PDF and XML download
* Automatic error handling and logging

Requirements:
-------------
* l10n_py_edi_base module must be installed
* FacturaSend account credentials (API Key and Tenant ID)

Configuration:
--------------
1. Go to Settings > Technical > System Parameters
2. Set l10n_py.edi_provider = 'facturasend'
3. Configure connector in Facturación Electrónica > Connectors
    """,
    'author': 'KMEE',
    'website': 'https://github.com/kmee',
    'license': 'LGPL-3',
    'depends': [
        'l10n_py_edi_base',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Views
        'views/facturasend_connector_views.xml',
        
        # Wizard
        'wizard/facturasend_connector_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

