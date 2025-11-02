{
    "name": "Paraguay - Electronic Invoicing Base",
    "version": "17.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "summary": "Base module for Electronic Invoicing in Paraguay",
    "description": """
Paraguay Electronic Invoicing Base Module
==========================================

This module provides the base functionality for electronic invoicing in Paraguay,
compliant with SET (Subsecretaría de Estado de Tributación) requirements.

Features:
---------
* Data models for electronic documents
* Field extensions for account.move, res.partner, res.company
* Validation of fiscal data (RUC, DV)
* JSON builder for electronic documents
* Support for multiple document types:
  - Factura Electrónica
  - Nota de Crédito Electrónica
  - Nota de Débito Electrónica
  - Nota de Remisión Electrónica
  - Autofactura Electrónica

Technical Information:
----------------------
* Compatible with SIFEN (Sistema Integrado de Facturación Electrónica Nacional)
* Prepared for integration with multiple EDI providers
* Support for contingency mode
* QR code and KUDE generation ready

This is the base module. You need to install a connector module:
- l10n_py_edi_factpy: For FactPy integration
- l10n_py_edi_facturasend: For FacturaSend integration
    """,
    "author": "Your Company",
    "website": "https://www.yourcompany.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "l10n_py",  # Paraguayan localization
        "product",
        "sale",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/l10n_py_edi_security.xml",
        # Data
        "data/l10n_py_departments.xml",
        "data/l10n_py_districts.xml",
        "data/l10n_py_cities.xml",
        "data/l10n_py_edi_document_types.xml",
        "data/ir_cron_data.xml",
        # Views
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/account_move_views.xml",
        "views/account_journal_views.xml",
        "views/product_template_views.xml",
        "views/l10n_py_edi_log_views.xml",
        # Wizards
        "wizard/account_move_send_edi_views.xml",
        "wizard/l10n_py_edi_cancel_wizard_views.xml",
        # Reports
        "report/kude_report_template.xml",
        "report/kude_report.xml",
        # Menus
        "views/l10n_py_edi_menu.xml",
    ],
    "demo": [
        "demo/res_partner_demo.xml",
        "demo/product_demo.xml",
    ],
    "external_dependencies": {
        "python": [
            "qrcode",
            "requests",
            "cryptography",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "assets": {
        "web.assets_backend": [
            "l10n_py_edi_base/static/src/js/edi_widget.js",
            "l10n_py_edi_base/static/src/scss/edi_styles.scss",
        ],
        "web.report_assets_common": [
            "l10n_py_edi_base/static/src/scss/kude_report.scss",
        ],
    },
}
