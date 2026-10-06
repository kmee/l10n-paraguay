# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_sale_order_data(
        self, name, partner, dest_company, direct_delivery_address
    ):
        """Bridge with purchase_sale_inter_company: the maquila rule lives in
        sale.order; here it only gets the products of the purchase order,
        which the sale order does not have yet when it is created."""
        vals = super()._prepare_sale_order_data(
            name, partner, dest_company, direct_delivery_address
        )
        rule_vals = self.env["sale.order"]._l10n_py_maquila_matrix_order_values(
            dest_company, partner, self.order_line.product_id
        )
        for key, value in rule_vals.items():
            vals.setdefault(key, value)
        if (
            rule_vals
            and self.incoterm_id
            and "incoterm" in self.env["sale.order"]._fields
        ):
            vals.setdefault("incoterm", self.incoterm_id.id)
        return vals
