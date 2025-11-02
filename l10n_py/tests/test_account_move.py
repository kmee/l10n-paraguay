from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install", "l10n_py")
class TestAccountMove(common.TransactionCase):
    """Testes para o modelo account.move (extensão paraguaia)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountMove = cls.env["account.move"]
        cls.Authorization = cls.env["account.authorization"]
        cls.Partner = cls.env["res.partner"]
        cls.Product = cls.env["product.product"]
        cls.Tax = cls.env["account.tax"]
        cls.Journal = cls.env["account.journal"]

        # Criar empresa
        cls.company = cls.env.ref("base.main_company")

        # Criar journal de vendas
        cls.journal = cls.Journal.search(
            [("type", "=", "sale"), ("company_id", "=", cls.company.id)], limit=1
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

        # Criar timbrado válido
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
                "document_type": "invoice",
                "company_id": cls.company.id,
            }
        )

        # Criar cliente
        cls.partner = cls.Partner.create(
            {
                "name": "Cliente Test PY",
                "ruc": "12345678-9",
                "taxpayer_type": "juridica",
            }
        )

        # Criar impostos
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

        # Criar produtos
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

    def test_01_create_invoice_with_authorization(self):
        """Teste de criação de fatura com timbrado"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        self.assertTrue(invoice.id, "Fatura deve ser criada")
        self.assertEqual(
            invoice.authorization_id,
            self.authorization,
            "Timbrado deve estar associado",
        )

    def test_02_compute_full_invoice_number(self):
        """Teste do cálculo do número completo da fatura"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        # Confirmar fatura para gerar número
        invoice.action_post()

        self.assertTrue(invoice.full_invoice_number, "Número completo deve ser gerado")
        self.assertIn(
            "001-001",
            invoice.full_invoice_number,
            "Número deve conter estabelecimento e ponto de expedição",
        )

    def test_03_compute_amount_iva_10(self):
        """Teste do cálculo de IVA 10%"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_10.id])],
                        },
                    )
                ],
            }
        )

        self.assertEqual(
            invoice.amount_subtotal_10, 100.0, "Subtotal IVA 10% deve ser 100"
        )
        self.assertEqual(invoice.amount_iva_10, 10.0, "IVA 10% deve ser 10")

    def test_04_compute_amount_iva_5(self):
        """Teste do cálculo de IVA 5%"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_5.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_5.id])],
                        },
                    )
                ],
            }
        )

        self.assertEqual(
            invoice.amount_subtotal_5, 100.0, "Subtotal IVA 5% deve ser 100"
        )
        self.assertEqual(invoice.amount_iva_5, 5.0, "IVA 5% deve ser 5")

    def test_05_compute_amount_exempt(self):
        """Teste do cálculo de valores exentos"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_exempt.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_exempt.id])],
                        },
                    )
                ],
            }
        )

        self.assertEqual(
            invoice.amount_subtotal_exempt, 100.0, "Subtotal exento deve ser 100"
        )
        self.assertEqual(invoice.amount_iva_total, 0.0, "IVA total deve ser 0")

    def test_06_compute_amount_iva_mixed(self):
        """Teste do cálculo de IVA com múltiplas alíquotas"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_10.id])],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_5.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_5.id])],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_exempt.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_exempt.id])],
                        },
                    ),
                ],
            }
        )

        self.assertEqual(
            invoice.amount_subtotal_10, 100.0, "Subtotal IVA 10% deve ser 100"
        )
        self.assertEqual(
            invoice.amount_subtotal_5, 100.0, "Subtotal IVA 5% deve ser 100"
        )
        self.assertEqual(
            invoice.amount_subtotal_exempt, 100.0, "Subtotal exento deve ser 100"
        )
        self.assertEqual(invoice.amount_iva_10, 10.0, "IVA 10% deve ser 10")
        self.assertEqual(invoice.amount_iva_5, 5.0, "IVA 5% deve ser 5")
        self.assertEqual(invoice.amount_iva_total, 15.0, "IVA total deve ser 15")

    def test_07_compute_amount_total_words(self):
        """Teste da conversão do total para letras"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_exempt.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_exempt.id])],
                        },
                    )
                ],
            }
        )

        self.assertTrue(
            invoice.amount_total_words, "Total em letras deve ser calculado"
        )
        self.assertIn(
            "guaraníes",
            invoice.amount_total_words.lower(),
            "Deve incluir a palavra guaraníes",
        )

    def test_08_post_without_authorization(self):
        """Teste de confirmação de fatura sem timbrado"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_09_post_with_authorization_assigns_number(self):
        """Teste de atribuição de número ao confirmar fatura"""
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        self.assertFalse(
            invoice.invoice_number, "Número não deve estar atribuído antes de confirmar"
        )

        invoice.action_post()

        self.assertTrue(
            invoice.invoice_number, "Número deve ser atribuído após confirmar"
        )
        self.assertEqual(invoice.invoice_number, 1, "Primeiro número deve ser 1")

    def test_10_post_sequential_numbers(self):
        """Teste de numeração sequencial"""
        invoice1 = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        invoice1.action_post()

        invoice2 = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        invoice2.action_post()

        self.assertEqual(
            invoice2.invoice_number,
            invoice1.invoice_number + 1,
            "Número da segunda fatura deve ser sequencial",
        )

    def test_11_post_with_expired_authorization(self):
        """Teste de confirmação com timbrado vencido"""
        today = date.today()
        expired_auth = self.Authorization.create(
            {
                "name": "99999999",
                "date_from": today - timedelta(days=400),
                "date_to": today - timedelta(days=35),
                "invoice_number_from": 1,
                "invoice_number_to": 1000,
                "establishment": "002",
                "expedition_point": "001",
                "document_type": "invoice",
            }
        )

        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "authorization_id": expired_auth.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_12_purchase_invoice_without_authorization(self):
        """Teste de que faturas de compra não exigem timbrado"""
        invoice = self.AccountMove.create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.Journal.search(
                    [("type", "=", "purchase")], limit=1
                ).id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_10.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        # Não deve lançar erro
        try:
            invoice.action_post()
            success = True
        except ValidationError:
            success = False

        self.assertTrue(success, "Faturas de compra não devem exigir timbrado")
