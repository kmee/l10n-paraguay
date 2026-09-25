# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Paraguay - Maquila Operations / MRP Bridge",
    "summary": "Compute the TUM VAN amount from Maquila MRP when both are installed",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-paraguay",
    "license": "AGPL-3",
    "depends": [
        "l10n_py_maquila_ops",
        "l10n_py_maquila_mrp",
    ],
    "data": [
        "views/maquila_tum_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
}
