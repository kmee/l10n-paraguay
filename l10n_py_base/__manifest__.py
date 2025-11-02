{
    "name": "Paraguay - Base Localization",
    "version": "17.0.1.0.0",
    "category": "Localization",
    "summary": "Base localization data for Paraguay",
    "description": """
Paraguay Base Localization
==========================

This module provides the basic localization data for Paraguay:

* RUC (Registro Único del Contribuyente) fields and validation
* Document types (Cédula, Passport, etc.)
* Taxpayer types (Contribuyente, No Contribuyente)
* Location data (Departments, Districts, Cities)
* Fiscal validation methods
* Partner fiscal data extensions

This is a base module required by other Paraguayan localization modules.
    """,
    "author": "KMEE",
    "website": "https://github.com/OCA/l10n-paraguay",
    "license": "LGPL-3",
    "depends": [
        "base",
        "base_address_extended",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Data - Orden importante: primero states, luego districts, luego cities
        "data/res_country_state_data.xml",
        "data/l10n_py_district_data.xml",
        "data/res_city_data.xml",
        # Views
        "views/res_partner_views.xml",
    ],
    "demo": [
        "demo/res_partner_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
