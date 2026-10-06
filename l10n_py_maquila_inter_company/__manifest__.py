# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Paraguay - Maquila Inter Company",
    "summary": "Link inter-company orders and bills to the maquila program",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Localization",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-paraguay",
    "license": "AGPL-3",
    "depends": [
        "l10n_py",
        "l10n_py_edi_base",
        "l10n_py_maquila_ops",
        "purchase_sale_inter_company",
        "account_invoice_inter_company",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
