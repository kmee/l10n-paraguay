# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

# Paraguayan document type of the documents of the Odoo accounting demo
DEMO_DOCUMENT_TYPES = {
    "out_invoice": "l10n_py_account.dc_py_f",
    "out_refund": "l10n_py_account.dc_py_nc",
    "in_invoice": "l10n_py_account.dc_py_f",
    "in_refund": "l10n_py_account.dc_py_nc",
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @api.model
    def _get_demo_data_move(self, company=False):
        """Make the Odoo accounting demo documents valid Paraguayan documents.

        Loading a chart with ``install_demo=True`` creates and posts invoices,
        credit notes and vendor bills. In a Paraguayan company the customer
        documents get the only timbrado of the company for their document
        type, the establishment and the expedition point of the sale journal,
        valid on the invoice date, so they are numbered by it; the vendor
        documents get the number of the supplier document. A customer document
        without exactly one such timbrado is left as the Odoo demo defines it.
        """
        move_data = super()._get_demo_data_move(company)
        company = company or self.env.company
        if company.account_fiscal_country_id.code != "PY":
            return move_data
        sale_journal = self.env["account.journal"].search(
            [
                *self.env["account.journal"]._check_company_domain(company),
                ("type", "=", "sale"),
            ],
            limit=1,
        )
        vendor_number = 100
        for vals in move_data.values():
            move_type = vals.get("move_type")
            if move_type not in DEMO_DOCUMENT_TYPES or not vals.get("invoice_date"):
                continue
            document_type = self.env.ref(DEMO_DOCUMENT_TYPES[move_type])
            if move_type in ("in_invoice", "in_refund"):
                vendor_number += 1
                vals["l10n_latam_document_type_id"] = document_type.id
                vals["l10n_latam_document_number"] = f"001-001-{vendor_number:07d}"
                continue
            invoice_date = fields.Date.to_date(vals["invoice_date"])
            authorization = self.env["account.authorization"].search(
                [
                    ("company_id", "=", company.id),
                    ("l10n_latam_document_type_id", "=", document_type.id),
                    ("establishment", "=", sale_journal.l10n_py_establishment),
                    ("expedition_point", "=", sale_journal.l10n_py_point),
                    ("date_from", "<=", invoice_date),
                    ("date_to", ">=", invoice_date),
                ]
            )
            if len(authorization) == 1:
                vals["l10n_latam_document_type_id"] = document_type.id
                vals["l10n_py_authorization_id"] = authorization.id
        return move_data
