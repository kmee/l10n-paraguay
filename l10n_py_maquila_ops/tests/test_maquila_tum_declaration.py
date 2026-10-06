# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestMaquilaTumDeclaration(AccountTestInvoicingCommon):
    """Ley 7547/2025 Art. 37 (value added components and 1% over the greater of
    value added and export invoice value) and Decreto 5714/2026 Art. 43
    (monthly declaration, due even without exports)."""

    # The module does not depend on a chart of accounts: use the generic one
    # instead of guessing it from the company country (l10n_py may be absent).
    # The test company is not Paraguayan: with the Paraguayan localization
    # installed the journals of a PY company require LATAM document types,
    # which is not what is tested. "Domestic" means the company country.
    chart_template = "generic_coa"
    country_code = "US"

    @classmethod
    def get_default_groups(cls):
        return super().get_default_groups() | cls.env.ref(
            "l10n_py_maquila_base.group_maquila_manager"
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.supplier_py = cls.env["res.partner"].create(
            {"name": "Proveedor Nacional", "country_id": cls.company.country_id.id}
        )
        cls.supplier_foreign = cls.env["res.partner"].create(
            {"name": "Foreign Supplier", "country_id": cls.env.ref("base.cn").id}
        )
        cls.matriz = cls.env["res.partner"].create(
            {"name": "Matriz BR", "country_id": cls.env.ref("base.br").id}
        )
        cls.goods = cls.env["product.product"].create(
            {"name": "Embalaje nacional", "type": "consu"}
        )
        cls.service = cls.env["product.product"].create(
            {"name": "Servicio de maquila", "type": "service"}
        )
        account_model = cls.env["account.account"]
        cls.salary_account = account_model.create(
            {"name": "Sueldos", "code": "TUMSAL", "account_type": "expense"}
        )
        cls.depreciation_account = account_model.create(
            {
                "name": "Depreciacion",
                "code": "TUMDEP",
                "account_type": "expense_depreciation",
            }
        )
        cls.tum_expense_account = account_model.create(
            {"name": "Tributo Unico", "code": "TUMEXP", "account_type": "expense"}
        )
        cls.tum_payable_account = account_model.create(
            {
                "name": "Tributo Unico a pagar",
                "code": "TUMPAY",
                "account_type": "liability_current",
            }
        )
        plan = cls.env["account.analytic.plan"].create({"name": "TUM Test Plan"})
        cls.analytic = cls.env["account.analytic.account"].create(
            {"name": "Programa TUM", "plan_id": plan.id, "company_id": cls.company.id}
        )
        cls.program = cls.env["l10n_py.maquila.program"].create(
            {
                "name": "Programa TUM",
                "code": "RES-TUM-001",
                "maquila_type": "pura",
                "matriz_partner_id": cls.matriz.id,
                "company_id": cls.company.id,
                "state": "active",
                "tum_salary_account_ids": [(6, 0, cls.salary_account.ids)],
                "tum_depreciation_account_ids": [(6, 0, cls.depreciation_account.ids)],
                "tum_expense_account_id": cls.tum_expense_account.id,
                "tum_payable_account_id": cls.tum_payable_account.id,
            }
        )

    # ---------- helpers ----------
    def _invoice(
        self,
        move_type,
        partner,
        product,
        amount,
        date="2026-09-10",
        program=True,
        analytic=None,
        post=True,
    ):
        line = {
            "product_id": product.id,
            "quantity": 1,
            "price_unit": amount,
            "tax_ids": [(6, 0, [])],
        }
        if analytic:
            line["analytic_distribution"] = analytic
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_date": date,
                "date": date,
                "l10n_py_maquila_program_id": program and self.program.id,
                "invoice_line_ids": [(0, 0, line)],
            }
        )
        if post:
            move.action_post()
        return move

    def _entry(self, account, amount, date="2026-09-30", program=True, analytic=None):
        debit = {"name": account.name, "account_id": account.id, "debit": amount}
        if analytic:
            debit["analytic_distribution"] = analytic
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": date,
                "journal_id": self.company_data["default_journal_misc"].id,
                "l10n_py_maquila_program_id": program and self.program.id,
                "line_ids": [
                    (0, 0, debit),
                    (
                        0,
                        0,
                        {
                            "name": account.name,
                            "account_id": self.tum_payable_account.id,
                            "credit": amount,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _declaration(self, date_from="2026-09-01"):
        declaration = self.env["l10n_py.maquila.tum.declaration"].create(
            {"program_id": self.program.id, "date_from": date_from}
        )
        declaration.action_compute()
        return declaration

    # ---------- components ----------
    def test_goods_and_services_from_domestic_bills(self):
        bill_goods = self._invoice("in_invoice", self.supplier_py, self.goods, 1000)
        bill_service = self._invoice("in_invoice", self.supplier_py, self.service, 300)
        self._invoice("in_refund", self.supplier_py, self.goods, 200)
        # Not value added: imported goods, other period, not linked to the
        # program, draft bill.
        self._invoice("in_invoice", self.supplier_foreign, self.goods, 5000)
        self._invoice(
            "in_invoice", self.supplier_py, self.goods, 700, date="2026-10-01"
        )
        self._invoice("in_invoice", self.supplier_py, self.goods, 900, program=False)
        self._invoice("in_invoice", self.supplier_py, self.goods, 400, post=False)
        declaration = self._declaration()
        self.assertEqual(declaration.amount_a, 800)
        self.assertEqual(declaration.amount_b, 300)
        self.assertEqual(declaration.value_added_amount, 1100)
        goods_line = declaration.line_ids.filtered(lambda x: x.move_id == bill_goods)
        self.assertEqual(goods_line.component, "a")
        self.assertEqual(goods_line.source, "auto")
        self.assertEqual(goods_line.partner_id, self.supplier_py)
        self.assertEqual(goods_line.amount, 1000)
        service_line = declaration.line_ids.filtered(
            lambda x: x.move_id == bill_service
        )
        self.assertEqual(service_line.component, "b")
        self.assertEqual(len(declaration.line_ids), 3)

    def test_analytic_share_of_bill(self):
        self.program.analytic_account_id = self.analytic
        self._invoice(
            "in_invoice",
            self.supplier_py,
            self.goods,
            1000,
            program=False,
            analytic={str(self.analytic.id): 40.0},
        )
        declaration = self._declaration()
        self.assertEqual(declaration.amount_a, 400)

    def test_salaries_and_depreciation_from_accounts(self):
        self.program.analytic_account_id = self.analytic
        self._entry(self.salary_account, 2000)
        self._entry(
            self.depreciation_account,
            400,
            program=False,
            analytic={str(self.analytic.id): 100.0},
        )
        # Salary of another activity: not linked to the program.
        self._entry(self.salary_account, 9000, program=False)
        declaration = self._declaration()
        self.assertEqual(declaration.amount_c, 2000)
        self.assertEqual(declaration.amount_d, 400)
        self.assertFalse(declaration.warning_message)

    def test_warning_without_salary_accounts(self):
        self.program.tum_salary_account_ids = [(5, 0, 0)]
        declaration = self._declaration()
        self.assertIn("component c)", declaration.warning_message)

    def test_service_remuneration_and_export_invoice(self):
        self._invoice("out_invoice", self.matriz, self.service, 1500)
        self._invoice("out_invoice", self.matriz, self.goods, 10000)
        declaration = self._declaration()
        self.assertEqual(declaration.amount_e, 1500)
        self.assertEqual(declaration.export_invoice_amount, 11500)
        self.assertEqual(len(declaration.export_invoice_ids), 2)
        # Export invoice value is greater than the value added.
        self.assertEqual(declaration.tax_base_origin, "export_invoice")
        self.assertEqual(declaration.tax_base, 11500)
        self.assertEqual(declaration.tax_amount, 115)

    def test_value_added_greater_than_export(self):
        self._invoice("in_invoice", self.supplier_py, self.goods, 6000)
        self._entry(self.salary_account, 8000)
        self._invoice("out_invoice", self.matriz, self.goods, 10000)
        declaration = self._declaration()
        self.assertEqual(declaration.value_added_amount, 14000)
        self.assertEqual(declaration.tax_base_origin, "value_added")
        self.assertEqual(declaration.tax_base, 14000)
        self.assertEqual(declaration.tax_amount, 140)

    def test_manual_lines_are_kept_and_identified(self):
        declaration = self._declaration()
        self.env["l10n_py.maquila.tum.declaration.line"].create(
            {
                "declaration_id": declaration.id,
                "component": "c",
                "name": "Planilla de sueldos 09/2026",
                "note": "Planilla IPS 09/2026",
                "amount": 700,
            }
        )
        self._entry(self.salary_account, 300)
        declaration.action_compute()
        self.assertEqual(declaration.amount_c, 1000)
        self.assertEqual(declaration.amount_manual, 700)
        manual = declaration.line_ids.filtered(lambda x: x.source == "manual")
        self.assertEqual(manual.amount, 700)
        with self.assertRaises(ValidationError):
            self.env["l10n_py.maquila.tum.declaration.line"].create(
                {
                    "declaration_id": declaration.id,
                    "component": "d",
                    "name": "Depreciacion sin soporte",
                    "amount": 100,
                }
            )

    def test_recompute_drops_stale_lines(self):
        bill = self._invoice("in_invoice", self.supplier_py, self.goods, 1000)
        declaration = self._declaration()
        self.assertEqual(declaration.amount_a, 1000)
        bill.button_draft()
        declaration.action_compute()
        self.assertEqual(declaration.amount_a, 0)
        self.assertFalse(declaration.line_ids)

    # ---------- monthly declaration ----------
    def test_month_without_operations_is_declared(self):
        declaration = self._declaration()
        self.assertEqual(declaration.value_added_amount, 0)
        self.assertEqual(declaration.export_invoice_amount, 0)
        self.assertEqual(declaration.tax_amount, 0)
        declaration.action_confirm()
        self.assertEqual(declaration.state, "confirmed")
        with self.assertRaises(UserError):
            declaration.action_generate_move()

    def test_confirm_requires_compute(self):
        declaration = self.env["l10n_py.maquila.tum.declaration"].create(
            {"program_id": self.program.id, "date_from": "2026-09-01"}
        )
        with self.assertRaises(UserError):
            declaration.action_confirm()

    def test_confirmed_declaration_is_locked(self):
        self._invoice("in_invoice", self.supplier_py, self.goods, 1000)
        declaration = self._declaration()
        declaration.action_confirm()
        with self.assertRaises(UserError):
            declaration.action_compute()
        with self.assertRaises(UserError):
            declaration.line_ids.write({"amount": 1})
        with self.assertRaises(UserError):
            declaration.unlink()

    def test_period_is_a_calendar_month(self):
        declaration = self._declaration("2024-02-01")
        self.assertEqual(str(declaration.date_to), "2024-02-29")
        self.assertEqual(declaration.name, "TUM RES-TUM-001 2024-02")
        with self.assertRaises(ValidationError):
            self.env["l10n_py.maquila.tum.declaration"].create(
                {"program_id": self.program.id, "date_from": "2026-09-15"}
            )
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            self.env["l10n_py.maquila.tum.declaration"].create(
                {"program_id": self.program.id, "date_from": "2024-02-01"}
            )
            self.env.flush_all()

    def test_generate_journal_entry(self):
        self._invoice("out_invoice", self.matriz, self.goods, 25000)
        declaration = self._declaration()
        declaration.action_confirm()
        declaration.action_generate_move()
        move = declaration.move_id
        self.assertEqual(move.l10n_py_maquila_program_id, self.program)
        self.assertEqual(str(move.date), "2026-09-30")
        debit = move.line_ids.filtered(lambda x: x.debit)
        credit = move.line_ids.filtered(lambda x: x.credit)
        self.assertEqual(debit.account_id, self.tum_expense_account)
        self.assertEqual(credit.account_id, self.tum_payable_account)
        self.assertEqual(debit.debit, 250)
        self.assertEqual(credit.credit, 250)
        with self.assertRaises(UserError):
            declaration.action_generate_move()
        declaration.action_draft()
        self.assertFalse(declaration.move_id)
        self.assertFalse(move.exists())

    def test_reset_blocked_by_posted_entry(self):
        self._invoice("out_invoice", self.matriz, self.goods, 25000)
        declaration = self._declaration()
        declaration.action_confirm()
        declaration.action_generate_move()
        declaration.move_id.action_post()
        with self.assertRaises(UserError):
            declaration.action_draft()

    def test_report_renders(self):
        self._invoice("in_invoice", self.supplier_py, self.goods, 1000)
        declaration = self._declaration()
        html = (
            self.env["ir.actions.report"]
            ._render_qweb_html(
                "l10n_py_maquila_ops.report_tum_declaration", declaration.ids
            )[0]
            .decode()
        )
        self.assertIn("RES-TUM-001", html)
        self.assertIn("Goods acquired in the country", html)
        self.assertIn("Proveedor Nacional", html)

    # ---------- TUM wizard and order flows ----------
    def test_tum_wizard_reads_value_added(self):
        self._invoice("in_invoice", self.supplier_py, self.goods, 6000)
        self._invoice("out_invoice", self.matriz, self.goods, 4000)
        wizard = self.env["l10n_py.maquila.tum.wizard"].create(
            {
                "program_id": self.program.id,
                "period_start": "2026-09-01",
                "period_end": "2026-09-30",
                "currency_id": self.company.currency_id.id,
            }
        )
        wizard.action_compute()
        self.assertEqual(wizard.van_amount, 6000)
        self.assertEqual(wizard.export_invoice_amount, 4000)
        self.assertEqual(wizard.tum_base, 6000)
        self.assertEqual(wizard.tum_amount, 60)
        action = wizard.action_open_declaration()
        declaration = self.env["l10n_py.maquila.tum.declaration"].browse(
            action["res_id"]
        )
        self.assertEqual(str(declaration.date_from), "2026-09-01")
        self.assertEqual(declaration.tax_amount, 60)

    def test_invoices_from_orders_carry_the_program(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.matriz.id,
                "l10n_py_maquila_program_id": self.program.id,
                "order_line": [
                    (0, 0, {"product_id": self.service.id, "product_uom_qty": 1})
                ],
            }
        )
        order.action_confirm()
        invoice = order._create_invoices()
        self.assertEqual(invoice.l10n_py_maquila_program_id, self.program)
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": self.supplier_py.id,
                "l10n_py_maquila_program_id": self.program.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.service.id,
                            "product_qty": 1,
                            "price_unit": 50,
                        },
                    )
                ],
            }
        )
        purchase.button_confirm()
        purchase.action_create_invoice()
        self.assertEqual(purchase.invoice_ids.l10n_py_maquila_program_id, self.program)
