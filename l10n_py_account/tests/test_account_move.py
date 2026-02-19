from datetime import date, timedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "l10n_py")
class TestAccountMove(TransactionCase):
    """Tests para account.move (extensión paraguaya)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountMove = cls.env["account.move"]
        cls.Authorization = cls.env["account.authorization"]
        cls.Partner = cls.env["res.partner"]
        cls.Product = cls.env["product.product"]
        cls.Tax = cls.env["account.tax"]
        cls.Journal = cls.env["account.journal"]

        cls.company = cls.env.ref("base.main_company")
        cls.country_py = cls.env.ref("base.py")

        # Tipo de documento factura
        cls.doc_type_invoice = cls.env["l10n_latam.document.type"].search(
            [("country_id", "=", cls.country_py.id), ("code", "=", "1")],
            limit=1,
        )
        if not cls.doc_type_invoice:
            cls.doc_type_invoice = cls.env["l10n_latam.document.type"].create(
                {
                    "name": "Factura",
                    "code": "1",
                    "country_id": cls.country_py.id,
                    "internal_type": "invoice",
                }
            )

        # Cuentas contables
        cls.account_income = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                ("account_type", "=", "income"),
            ],
            limit=1,
        )
        if not cls.account_income:
            cls.account_income = cls.env["account.account"].create(
                {
                    "name": "Ingresos por Ventas",
                    "code": "400001",
                    "account_type": "income",
                    "company_id": cls.company.id,
                }
            )

        cls.account_receivable = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                ("account_type", "=", "asset_receivable"),
            ],
            limit=1,
        )
        if not cls.account_receivable:
            cls.account_receivable = cls.env["account.account"].create(
                {
                    "name": "Cuentas por Cobrar",
                    "code": "110001",
                    "account_type": "asset_receivable",
                    "reconcile": True,
                    "company_id": cls.company.id,
                }
            )

        # Journal de ventas
        cls.journal = cls.Journal.search(
            [("type", "=", "sale"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        if not cls.journal:
            cls.journal = cls.Journal.create(
                {
                    "name": "Ventas",
                    "type": "sale",
                    "code": "VEN",
                    "company_id": cls.company.id,
                }
            )

        # Timbrado válido
        today = date.today()
        cls.authorization = cls.Authorization.create(
            {
                "name": "12345678",
                "date_from": today - timedelta(days=30),
                "date_to": today + timedelta(days=335),
                "invoice_number_from": 1,
                "invoice_number_to": 10000,
                "establishment": "001",
                "expedition_point": "001",
                "l10n_latam_document_type_id": cls.doc_type_invoice.id,
                "company_id": cls.company.id,
            }
        )

        # Cliente
        cls.partner = cls.Partner.create(
            {
                "name": "Cliente Test PY",
                "country_id": cls.country_py.id,
                "property_account_receivable_id": cls.account_receivable.id,
                "property_account_payable_id": cls.account_receivable.id,
            }
        )

        # Impuestos
        cls.tax_10 = cls.Tax.create(
            {
                "name": "IVA 10%",
                "amount": 10.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        cls.tax_5 = cls.Tax.create(
            {
                "name": "IVA 5%",
                "amount": 5.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        cls.tax_exempt = cls.Tax.create(
            {
                "name": "Exento",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )

        # Productos
        cls.product_10 = cls.Product.create(
            {
                "name": "Producto IVA 10%",
                "list_price": 100.0,
                "taxes_id": [(6, 0, [cls.tax_10.id])],
            }
        )
        cls.product_5 = cls.Product.create(
            {
                "name": "Producto IVA 5%",
                "list_price": 100.0,
                "taxes_id": [(6, 0, [cls.tax_5.id])],
            }
        )
        cls.product_exempt = cls.Product.create(
            {
                "name": "Producto Exento",
                "list_price": 100.0,
                "taxes_id": [(6, 0, [cls.tax_exempt.id])],
            }
        )

    def _create_invoice(self, products_taxes=None, **kwargs):
        """Helper para crear factura de prueba"""
        if products_taxes is None:
            products_taxes = [(self.product_10, self.tax_10)]

        lines = []
        for product, tax in products_taxes:
            lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "quantity": 1,
                        "price_unit": 100.0,
                        "tax_ids": [(6, 0, [tax.id])],
                        "account_id": self.account_income.id,
                    },
                )
            )

        vals = {
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "journal_id": self.journal.id,
            "l10n_py_authorization_id": self.authorization.id,
            "invoice_line_ids": lines,
        }
        vals.update(kwargs)
        return self.AccountMove.create(vals)

    def test_authorization_field_exists(self):
        """l10n_py_authorization_id en el move"""
        invoice = self._create_invoice()
        self.assertEqual(invoice.l10n_py_authorization_id, self.authorization)

    def test_iva_breakdown_10(self):
        """IVA 10% subtotal e impuesto calculados"""
        invoice = self._create_invoice(products_taxes=[(self.product_10, self.tax_10)])
        self.assertEqual(invoice.l10n_py_amount_subtotal_10, 100.0)
        self.assertAlmostEqual(invoice.l10n_py_amount_iva_10, 10.0, places=2)

    def test_iva_breakdown_5(self):
        """IVA 5% subtotal e impuesto calculados"""
        invoice = self._create_invoice(products_taxes=[(self.product_5, self.tax_5)])
        self.assertEqual(invoice.l10n_py_amount_subtotal_5, 100.0)
        self.assertAlmostEqual(invoice.l10n_py_amount_iva_5, 5.0, places=2)

    def test_iva_exempt(self):
        """Valor exento calculado"""
        invoice = self._create_invoice(
            products_taxes=[(self.product_exempt, self.tax_exempt)]
        )
        self.assertEqual(invoice.l10n_py_amount_exempt, 100.0)
        self.assertEqual(invoice.l10n_py_amount_iva_total, 0.0)

    def test_iva_mixed(self):
        """Factura con IVA 10% + 5% + exento"""
        invoice = self._create_invoice(
            products_taxes=[
                (self.product_10, self.tax_10),
                (self.product_5, self.tax_5),
                (self.product_exempt, self.tax_exempt),
            ]
        )
        self.assertEqual(invoice.l10n_py_amount_subtotal_10, 100.0)
        self.assertEqual(invoice.l10n_py_amount_subtotal_5, 100.0)
        self.assertEqual(invoice.l10n_py_amount_exempt, 100.0)
        self.assertAlmostEqual(invoice.l10n_py_amount_iva_10, 10.0, places=2)
        self.assertAlmostEqual(invoice.l10n_py_amount_iva_5, 5.0, places=2)
        self.assertAlmostEqual(invoice.l10n_py_amount_iva_total, 15.0, places=2)

    def test_full_invoice_number_format(self):
        """Formato 001-001-0000001"""
        invoice = self._create_invoice(l10n_py_invoice_number=1)
        self.assertEqual(invoice.l10n_py_full_invoice_number, "001-001-0000001")

    def test_amount_total_words(self):
        """Total en letras en español"""
        invoice = self._create_invoice(
            products_taxes=[(self.product_exempt, self.tax_exempt)]
        )
        self.assertTrue(invoice.l10n_py_amount_total_words)
