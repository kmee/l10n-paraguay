{
    "name": "Paraguay - SIFEN Direct EDI Connector",
    "version": "16.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "summary": "Direct SIFEN transmission via pysifen library",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-paraguay",
    "license": "LGPL-3",
    "depends": ["l10n_py_edi_base"],
    "external_dependencies": {"python": ["sifen"]},
    "data": [
        "security/ir.model.access.csv",
        "views/edi_connector_views.xml",
        "views/res_company_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
