# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged("post_install", "-at_install")
class TestMaquilaInterCompany(TransactionCase):
    """Brazilian matrix buys from a Paraguayan maquiladora in the same
    database: the purchase order becomes a sale order under the maquila
    program, and the export invoice becomes the matrix vendor bill."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.usd = cls.env.ref("base.USD")
        (cls.usd | cls.env.ref("base.BRL") | cls.env.ref("base.PYG")).active = True
        cls.incoterm = cls.env.ref("account.incoterm_FCA")

        cls.br_company = cls._create_company(
            "Matriz BR (test)", "base.br", "base.BRL", "generic_coa"
        )
        cls.br_company.partner_id.street = "Rua das Flores, 100"
        cls.py_company = cls._create_company(
            "Maquiladora PY (test)", "base.py", "base.PYG", "py"
        )
        cls.py_company.l10n_py_is_maquiladora = True

        # Users: nobody below is a superuser or has access to both companies.
        cls.br_buyer = cls._create_user(
            "br_buyer", cls.br_company, "purchase.group_purchase_user"
        )
        cls.br_ic_user = cls._create_user(
            "br_ic_bill", cls.br_company, "account.group_account_invoice"
        )
        cls.py_ic_user = cls._create_user(
            "py_ic_sale",
            cls.py_company,
            "sales_team.group_sale_salesman,stock.group_stock_user,"
            "l10n_py_maquila_base.group_maquila_user",
        )
        cls.py_billing = cls._create_user(
            "py_billing",
            cls.py_company,
            "sales_team.group_sale_salesman_all_leads,account.group_account_invoice",
        )
        cls.py_company.write(
            {
                "so_from_po": True,
                "sale_auto_validation": True,
                "intercompany_sale_user_id": cls.py_ic_user.id,
            }
        )
        cls.br_company.write(
            {
                "invoice_auto_validation": True,
                "intercompany_invoice_user_id": cls.br_ic_user.id,
            }
        )

        cls.py_vat10 = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.py_company.id),
                ("type_tax_use", "=", "sale"),
                ("amount", "=", 10),
                ("l10n_py_iva_affectation", "=", "1"),
            ],
            limit=1,
        )
        cls.product = cls._create_product("Perfil de aluminio (test)", "76042920")
        cls.other_product = cls._create_product("Placa LED (test)", "85395200")

        # The maquiladora sells to the matrix in USD.
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Matriz USD (test)",
                "currency_id": cls.usd.id,
                "company_id": cls.py_company.id,
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "0_product_variant",
                            "product_id": product.id,
                            "compute_price": "fixed",
                            "fixed_price": price,
                        }
                    )
                    for product, price in (
                        (cls.product, 150.0),
                        (cls.other_product, 80.0),
                    )
                ],
            }
        )
        cls.br_company.partner_id.with_company(
            cls.py_company
        ).property_product_pricelist = cls.pricelist

        # Timbrado for the export invoice.
        authorization = cls.env["account.authorization"].create(
            {
                "name": "12345678",
                "date_from": fields.Date.today() - timedelta(days=30),
                "date_to": fields.Date.today() + timedelta(days=300),
                "invoice_number_from": 1,
                "invoice_number_to": 1000,
                "establishment": "001",
                "expedition_point": "001",
                "l10n_latam_document_type_id": cls.env.ref(
                    "l10n_py_account.dc_py_f"
                ).id,
                "company_id": cls.py_company.id,
            }
        )
        cls.env["account.journal"].search(
            [("company_id", "=", cls.py_company.id), ("type", "=", "sale")]
        ).l10n_py_authorization_id = authorization

        cls.agreement = cls.env["agreement"].create(
            {"name": "CNIME Matriz BR (test)", "code": "CNIME-TEST-1"}
        )
        Program = cls.env["l10n_py.maquila.program"]
        common = {"maquila_type": "pura", "company_id": cls.py_company.id}
        cls.program = Program.create(
            dict(
                common,
                name="Perfiles",
                code="RES-BIM-B",
                state="active",
                matriz_partner_id=cls.br_company.partner_id.id,
                agreement_id=cls.agreement.id,
                product_line_ids=[Command.create({"product_id": cls.product.id})],
            )
        )
        # Sorted first by code, active, same matrix, but does not list the
        # product: must lose against the program that covers the order.
        cls.program_not_covering = Program.create(
            dict(
                common,
                name="Placas",
                code="RES-BIM-A",
                state="active",
                matriz_partner_id=cls.br_company.partner_id.id,
                product_line_ids=[Command.create({"product_id": cls.other_product.id})],
            )
        )
        cls.program_draft = Program.create(
            dict(
                common,
                name="Draft",
                code="RES-BIM-0",
                state="draft",
                matriz_partner_id=cls.br_company.partner_id.id,
            )
        )
        other_matrix = cls.env["res.partner"].create(
            {"name": "Other matrix", "country_id": cls.env.ref("base.ar").id}
        )
        cls.program_other_matrix = Program.create(
            dict(
                common,
                name="Other matrix",
                code="RES-BIM-00",
                state="active",
                matriz_partner_id=other_matrix.id,
            )
        )

    @classmethod
    def _create_company(cls, name, country_xmlid, currency_xmlid, chart):
        company = cls.env["res.company"].create(
            {
                "name": name,
                "country_id": cls.env.ref(country_xmlid).id,
                "currency_id": cls.env.ref(currency_xmlid).id,
            }
        )
        cls.env["account.chart.template"].try_loading(
            chart, company=company, install_demo=False
        )
        return company

    @classmethod
    def _create_user(cls, login, company, groups):
        return new_test_user(
            cls.env,
            login=login,
            groups="base.group_user," + groups,
            company_id=company.id,
            company_ids=[Command.set(company.ids)],
            email=f"{login}@example.com",
        )

    @classmethod
    def _create_product(cls, name, ncm):
        return cls.env["product.product"].create(
            {
                "name": name,
                "type": "consu",
                "company_id": False,
                "l10n_py_ncm_code": ncm,
                "taxes_id": [Command.set(cls.py_vat10.ids)],
                "supplier_taxes_id": [Command.clear()],
            }
        )

    def _confirm_purchase(self, products):
        po = (
            self.env["purchase.order"]
            .with_user(self.br_buyer)
            .create(
                {
                    "partner_id": self.py_company.partner_id.id,
                    "currency_id": self.usd.id,
                    "incoterm_id": self.incoterm.id,
                    "order_line": [
                        Command.create(
                            {"product_id": p.id, "product_qty": 10, "price_unit": 1}
                        )
                        for p in products
                    ],
                }
            )
        )
        po.button_confirm()
        return po

    def test_purchase_creates_maquila_export_sale(self):
        po = self._confirm_purchase(self.product)
        so = po.sudo().intercompany_sale_order_id
        self.assertTrue(so, "the PO must generate a sale order in the maquiladora")
        self.assertEqual(so.company_id, self.py_company)
        self.assertEqual(so.state, "sale")
        self.assertEqual(so.client_order_ref, po.name)
        self.assertEqual(so.l10n_py_maquila_program_id, self.program)
        self.assertEqual(so.l10n_py_maquila_agreement_id, self.agreement)
        self.assertTrue(so.fiscal_position_id.l10n_py_is_export)
        self.assertEqual(so.fiscal_position_id.company_id, self.py_company)
        self.assertEqual(
            so.order_line.tax_id.mapped("l10n_py_iva_affectation"),
            ["2"],
            "IVA 10% must be mapped to Exonerado on the export order",
        )
        self.assertEqual(so.currency_id, self.usd)
        self.assertEqual(so.incoterm, self.incoterm)
        # Price of the maquiladora is synced back to the matrix PO.
        self.assertEqual(po.order_line.price_unit, 150.0)

    def test_partner_fiscal_position_is_kept(self):
        domestic_fpos = self.env["account.fiscal.position"].create(
            {"name": "Manual position (test)", "company_id": self.py_company.id}
        )
        self.br_company.partner_id.with_company(
            self.py_company
        ).property_account_position_id = domestic_fpos
        so = self._confirm_purchase(self.product).sudo().intercompany_sale_order_id
        self.assertEqual(so.l10n_py_maquila_program_id, self.program)
        self.assertEqual(so.fiscal_position_id, domestic_fpos)

    def test_no_active_program_leaves_a_note(self):
        (self.program | self.program_not_covering).state = "suspended"
        so = self._confirm_purchase(self.product).sudo().intercompany_sale_order_id
        self.assertTrue(so)
        self.assertFalse(so.l10n_py_maquila_program_id)
        self.assertIn(
            "No active maquila program",
            "".join(so.message_ids.mapped("body")),
        )

    def test_products_outside_program_leave_a_note(self):
        so = (
            self._confirm_purchase(self.product | self.other_product)
            .sudo()
            .intercompany_sale_order_id
        )
        # Neither program covers both products: the first one is used and
        # the order says which product is missing.
        self.assertEqual(so.l10n_py_maquila_program_id, self.program_not_covering)
        bodies = "".join(so.message_ids.mapped("body"))
        self.assertIn("Products not listed in maquila program", bodies)
        self.assertIn(self.product.name, bodies)
        self.assertNotIn(self.other_product.name, bodies)

    def test_export_invoice_creates_matrix_vendor_bill(self):
        po = self._confirm_purchase(self.product)
        so = po.sudo().intercompany_sale_order_id
        invoice = so.with_user(self.py_billing)._create_invoices()
        invoice.with_user(self.py_billing).action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertTrue(invoice.l10n_py_full_invoice_number)
        self.assertEqual(invoice.l10n_py_amount_exonerado, 1500.0)
        self.assertEqual(invoice.amount_tax, 0.0)

        bill = (
            self.env["account.move"]
            .sudo()
            .search([("auto_invoice_id", "=", invoice.id)])
        )
        self.assertEqual(len(bill), 1)
        self.assertEqual(bill.company_id, self.br_company)
        self.assertEqual(bill.move_type, "in_invoice")
        self.assertEqual(bill.state, "posted", "totals match: auto-validated")
        self.assertEqual(bill.partner_id, self.py_company.partner_id)
        self.assertEqual(bill.currency_id, self.usd)
        self.assertEqual(bill.amount_total, 1500.0)
        self.assertEqual(bill.invoice_incoterm_id, self.incoterm)
        self.assertEqual(bill.ref, invoice.l10n_py_full_invoice_number)
        self.assertEqual(
            bill.l10n_py_source_document_number, invoice.l10n_py_full_invoice_number
        )
        self.assertEqual(bill.invoice_line_ids.l10n_py_source_ncm_code, "76042920")
        self.assertEqual(bill.invoice_line_ids.purchase_line_id, po.order_line)
        # The matrix user reads the PY references without access to the
        # maquiladora company.
        bill_as_br = bill.with_user(self.br_ic_user).with_company(self.br_company)
        self.assertEqual(
            bill_as_br.l10n_py_source_document_number,
            invoice.l10n_py_full_invoice_number,
        )

    def test_rule_without_inter_company_engine(self):
        """The maquila rule only depends on the data: a sale order typed by a
        salesman of the maquiladora for the matrix company gets the same
        program and export fiscal position, without any purchase order."""
        so = (
            self.env["sale.order"]
            .with_user(self.py_ic_user)
            .with_company(self.py_company)
            .create(
                {
                    "partner_id": self.br_company.partner_id.id,
                    "order_line": [Command.create({"product_id": self.product.id})],
                }
            )
        )
        self.assertEqual(so.l10n_py_maquila_program_id, self.program)
        self.assertTrue(so.fiscal_position_id.l10n_py_is_export)
        self.assertEqual(so.order_line.tax_id.mapped("l10n_py_iva_affectation"), ["2"])

    def test_rule_ignores_customers_that_are_not_the_matrix(self):
        foreign = self.env["res.partner"].create(
            {"name": "Foreign customer", "country_id": self.env.ref("base.br").id}
        )
        so = (
            self.env["sale.order"]
            .with_user(self.py_ic_user)
            .with_company(self.py_company)
            .create(
                {
                    "partner_id": foreign.id,
                    "order_line": [Command.create({"product_id": self.product.id})],
                }
            )
        )
        self.assertFalse(so.l10n_py_maquila_program_id)
        so.action_confirm()
        invoice = so.with_user(self.py_billing)._create_invoices()
        invoice.with_user(self.py_billing).action_post()
        self.assertTrue(invoice.l10n_py_full_invoice_number)
        self.assertEqual(invoice._l10n_py_maquila_matrix_bill_values(), {})
