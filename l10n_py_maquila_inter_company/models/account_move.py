# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_py_source_document_number = fields.Char(
        related="auto_invoice_id.l10n_py_full_invoice_number",
        string="Supplier Document Number (PY)",
        help="Number (establishment-point-number) of the Paraguayan document "
        "that generated this inter-company bill.",
    )
    l10n_py_source_cdc = fields.Char(
        related="auto_invoice_id.l10n_py_cdc",
        string="Supplier CDC (PY)",
        help="SIFEN control code of the Paraguayan document that generated "
        "this inter-company bill. Empty until the document is sent to SIFEN.",
    )

    # ------------------------------------------------------------------
    # Maquila rule, independent of the inter-company engine: what the vendor
    # bill of the matrix company keeps from the maquiladora document.
    # ------------------------------------------------------------------

    def _l10n_py_maquila_is_matrix_document(self):
        """Document of a maquiladora whose partner is another company of the
        same database (the foreign matrix)."""
        self.ensure_one()
        return bool(
            self.env["sale.order"]._l10n_py_maquila_matrix_company(
                self.company_id, self.commercial_partner_id
            )
        )

    def _l10n_py_maquila_matrix_bill_values(self):
        """Header values of the matrix vendor bill generated from this
        maquiladora invoice: Paraguayan fiscal number as bill reference,
        currency and Incoterm."""
        self.ensure_one()
        if not self._l10n_py_maquila_is_matrix_document():
            return {}
        vals = {"currency_id": self.currency_id.id}
        if self.l10n_py_full_invoice_number:
            vals["ref"] = self.l10n_py_full_invoice_number
        if self.invoice_incoterm_id:
            vals["invoice_incoterm_id"] = self.invoice_incoterm_id.id
        return vals

    def _prepare_invoice_data(self, dest_company):
        """Bridge with account_invoice_inter_company."""
        vals = super()._prepare_invoice_data(dest_company)
        vals.update(self._l10n_py_maquila_matrix_bill_values())
        return vals


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_py_source_ncm_code = fields.Char(
        string="NCM (supplier)",
        size=8,
        readonly=True,
        copy=False,
        help="NCM code of the product as declared in the Paraguayan document "
        "that generated this inter-company line.",
    )

    def _l10n_py_maquila_matrix_bill_line_values(self):
        """Line values of the matrix vendor bill: the NCM declared by the
        maquiladora."""
        self.ensure_one()
        ncm = self.product_id.l10n_py_ncm_code
        if not (ncm and self.move_id._l10n_py_maquila_is_matrix_document()):
            return {}
        return {"l10n_py_source_ncm_code": ncm}

    @api.model
    def _prepare_account_move_line(self, dest_move, dest_company):
        """Bridge with account_invoice_inter_company."""
        vals = super()._prepare_account_move_line(dest_move, dest_company)
        vals.update(self._l10n_py_maquila_matrix_bill_line_values())
        return vals
