# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup, escape

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    l10n_py_maquila_agreement_id = fields.Many2one(
        related="l10n_py_maquila_program_id.agreement_id",
        string="CNIME Contract",
    )

    # ------------------------------------------------------------------
    # Maquila rule: a maquiladora selling to its foreign matrix, when the
    # matrix is another company of the same database. It only looks at the
    # data (selling company, customer), so any inter-company engine, or a
    # user creating the order by hand, gets the same result.
    # ------------------------------------------------------------------

    @api.model
    def _l10n_py_maquila_matrix_company(self, company, partner):
        """Company of the database represented by ``partner`` when
        ``company`` is a maquiladora selling to it, else an empty record."""
        companies = self.env["res.company"]
        if not (company and partner and company.l10n_py_is_maquiladora):
            return companies
        return (
            companies.sudo()
            .search([("partner_id", "=", partner.commercial_partner_id.id)], limit=1)
            .filtered(lambda c: c != company)
        )

    @api.model
    def _l10n_py_maquila_find_program(self, company, matrix, products=None):
        """Active maquila program of ``company`` whose foreign matrix is the
        company ``matrix``. When several programs match, prefer the one whose
        product list covers all ``products``."""
        programs = (
            self.env["l10n_py.maquila.program"]
            .sudo()
            .search(
                [
                    ("company_id", "=", company.id),
                    ("state", "=", "active"),
                    (
                        "matriz_partner_id.commercial_partner_id",
                        "=",
                        matrix.partner_id.commercial_partner_id.id,
                    ),
                ]
            )
        )
        if products:
            covering = programs.filtered(
                lambda p: not (products - p.product_line_ids.product_id)
            )
            programs = covering or programs
        return programs[:1]

    @api.model
    def _l10n_py_maquila_export_fiscal_position(self, company, partner):
        """Fiscal position of an export of ``company`` to ``partner``.

        The core, with the l10n_py export ranking, already resolves the
        chart's export position for a foreign partner; the explicit export
        position is only a fallback when nothing is resolved, so a position
        configured on the partner is never replaced."""
        fpos_model = self.env["account.fiscal.position"].sudo().with_company(company)
        fpos = fpos_model._get_fiscal_position(partner)
        if fpos or partner.country_id == company.country_id:
            return fpos
        return fpos_model.search(
            [("company_id", "=", company.id), ("l10n_py_is_export", "=", True)],
            limit=1,
        )

    @api.model
    def _l10n_py_maquila_matrix_order_values(self, company, partner, products=None):
        """Values of a sale order of ``company`` to ``partner`` when it is a
        maquila sale to the matrix company: program and fiscal position."""
        matrix = self._l10n_py_maquila_matrix_company(company, partner)
        if not matrix:
            return {}
        program = self._l10n_py_maquila_find_program(company, matrix, products)
        if not program:
            return {}
        vals = {"l10n_py_maquila_program_id": program.id}
        fpos = self._l10n_py_maquila_export_fiscal_position(company, partner)
        if fpos:
            vals["fiscal_position_id"] = fpos.id
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("l10n_py_maquila_program_id") or not vals.get("partner_id"):
                continue
            company = (
                self.env["res.company"].browse(vals["company_id"])
                if vals.get("company_id")
                else self.env.company
            )
            partner = self.env["res.partner"].browse(vals["partner_id"])
            products = self.env["product.product"].browse(
                [
                    cmd[2]["product_id"]
                    for cmd in vals.get("order_line") or []
                    if isinstance(cmd, list | tuple)
                    and len(cmd) > 2
                    and isinstance(cmd[2], dict)
                    and cmd[2].get("product_id")
                ]
            )
            for key, value in self._l10n_py_maquila_matrix_order_values(
                company, partner, products
            ).items():
                vals.setdefault(key, value)
        return super().create(vals_list)

    def action_confirm(self):
        for order in self:
            if order._l10n_py_maquila_matrix_company(
                order.company_id, order.partner_id
            ):
                order._l10n_py_post_maquila_program_check()
        return super().action_confirm()

    def _l10n_py_post_maquila_program_check(self):
        """Leave a note on a sale to the matrix company when the maquila
        program is missing or does not list some of the ordered products.

        It is a warning, not an error: the order still confirms (and the
        purchase order of the matrix too, when the order was generated by
        an inter-company rule)."""
        self.ensure_one()
        program = self.l10n_py_maquila_program_id.sudo()
        if not program:
            body = self.env._(
                "No active maquila program of %(company)s has %(matrix)s as "
                "foreign matrix. Set the program manually before exporting.",
                company=self.company_id.name,
                matrix=self.partner_id.commercial_partner_id.name,
            )
            self.sudo().message_post(body=body)
            return
        if not program.product_line_ids:
            return
        missing = self.order_line.product_id - program.product_line_ids.product_id
        if missing:
            body = Markup("%s<ul>%s</ul>") % (
                self.env._(
                    "Products not listed in maquila program %(program)s:",
                    program=program.display_name,
                ),
                Markup().join(
                    Markup("<li>%s</li>") % escape(p.display_name) for p in missing
                ),
            )
            self.sudo().message_post(body=body)
