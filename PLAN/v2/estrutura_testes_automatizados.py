# ESTRUTURA DE TESTES AUTOMATIZADOS
# Módulos de Localização Paraguaia

"""
Este arquivo define uma estrutura completa de testes automatizados
para validar todas as funcionalidades dos módulos de localização paraguaia.
"""

# =============================================================================
# CONFIGURAÇÃO DE TESTES
# =============================================================================

import re
import unittest
from datetime import date, datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


class TestL10nPyBase(common.TransactionCase):
    """Classe base para testes da localização paraguaia"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configurar empresa
        cls.company = cls.env.ref("base.main_company")
        cls.company.write(
            {
                "name": "Empresa Test PY",
                "l10n_py_ruc": "12345678-9",
                "country_id": cls.env.ref("base.py").id,
            }
        )

        # Criar impostos paraguaios
        cls.tax_iva_10 = cls.env["account.tax"].create(
            {
                "name": "IVA 10%",
                "amount": 10.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": cls.company.id,
            }
        )

        cls.tax_iva_5 = cls.env["account.tax"].create(
            {
                "name": "IVA 5%",
                "amount": 5.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": cls.company.id,
            }
        )

        cls.tax_exento = cls.env["account.tax"].create(
            {
                "name": "Exento",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": cls.company.id,
            }
        )

        # Criar diário de vendas
        cls.journal_sales = cls.env["account.journal"].create(
            {
                "name": "Ventas Paraguay",
                "type": "sale",
                "code": "VPY",
                "company_id": cls.company.id,
                "l10n_py_establishment": "001",
                "l10n_py_expedition_point": "001",
            }
        )

        # Criar autorização (timbrado)
        today = date.today()
        cls.authorization = cls.env["account.authorization"].create(
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

        # Criar produtos de teste
        cls.product_gravado = cls.env["product.product"].create(
            {
                "name": "Producto Gravado 10%",
                "list_price": 100.0,
                "taxes_id": [(6, 0, [cls.tax_iva_10.id])],
            }
        )

        cls.product_reducido = cls.env["product.product"].create(
            {
                "name": "Producto Reducido 5%",
                "list_price": 50.0,
                "taxes_id": [(6, 0, [cls.tax_iva_5.id])],
            }
        )

        cls.product_exento = cls.env["product.product"].create(
            {
                "name": "Producto Exento",
                "list_price": 25.0,
                "taxes_id": [(6, 0, [cls.tax_exento.id])],
            }
        )


# =============================================================================
# TESTES DE VALIDAÇÃO DE RUC
# =============================================================================


@tagged("post_install", "-at_install", "l10n_py", "ruc")
class TestRUCValidation(TestL10nPyBase):
    """Testes para validação de RUC paraguaio"""

    def test_ruc_format_valid(self):
        """Testar formatos válidos de RUC"""
        valid_rucs = ["1234567-8", "12345678-9", "123456-7", "80012345-6"]

        for ruc in valid_rucs:
            with self.subTest(ruc=ruc):
                partner = self.env["res.partner"].create(
                    {
                        "name": f"Test Partner {ruc}",
                        "l10n_py_ruc": ruc,
                        "l10n_py_taxpayer_type": "2",
                    }
                )
                self.assertTrue(partner.id, f"RUC válido não foi aceito: {ruc}")

    def test_ruc_format_invalid(self):
        """Testar formatos inválidos de RUC"""
        invalid_rucs = [
            "12345",  # Muito curto
            "123456789",  # Muito longo
            "1234567A-8",  # Contém letra
            "1234567-AB",  # DV inválido
            "1234567--8",  # Hífen duplo
            "",  # Vazio
            "1234567-12",  # DV com 2 dígitos
        ]

        for ruc in invalid_rucs:
            with self.subTest(ruc=ruc):
                with self.assertRaises(ValidationError):
                    self.env["res.partner"].create(
                        {
                            "name": f"Test Partner {ruc}",
                            "l10n_py_ruc": ruc,
                            "l10n_py_taxpayer_type": "2",
                        }
                    )

    def test_ruc_check_digit_calculation(self):
        """Testar cálculo do dígito verificador"""
        # Casos conhecidos com DV correto
        test_cases = [
            ("1234567", "8"),
            ("8001234", "5"),
            ("987654", "3"),
        ]

        for ruc_number, expected_dv in test_cases:
            with self.subTest(ruc=ruc_number):
                from odoo.addons.l10n_py_core.validators.ruc_validator import (
                    RUCValidator,
                )

                calculated_dv = RUCValidator._calculate_check_digit(ruc_number)
                self.assertEqual(
                    str(calculated_dv),
                    expected_dv,
                    f"DV incorreto para {ruc_number}. Esperado: {expected_dv}, Calculado: {calculated_dv}",
                )

    def test_ruc_formatting(self):
        """Testar formatação automática de RUC"""
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "l10n_py_ruc": "12345678",  # Sem hífen
                "l10n_py_taxpayer_type": "2",
            }
        )

        # Deve formatar automaticamente
        self.assertIn(
            "-", partner.l10n_py_ruc, "RUC deve ser formatado automaticamente"
        )

    def test_ruc_search(self):
        """Testar busca por RUC"""
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner RUC Search",
                "l10n_py_ruc": "12345678-9",
                "l10n_py_taxpayer_type": "2",
            }
        )

        # Buscar por RUC completo
        found = self.env["res.partner"].search([("l10n_py_ruc", "=", "12345678-9")])
        self.assertIn(
            partner, found, "Busca por RUC completo deve encontrar o parceiro"
        )

        # Buscar por RUC sem formatação
        found = self.env["res.partner"].search([("l10n_py_ruc", "ilike", "123456789")])
        self.assertIn(
            partner, found, "Busca por RUC sem hífen deve encontrar o parceiro"
        )


# =============================================================================
# TESTES DE GERAÇÃO DE CDC
# =============================================================================


@tagged("post_install", "-at_install", "l10n_py", "cdc")
class TestCDCGeneration(TestL10nPyBase):
    """Testes para geração de CDC (Código de Control)"""

    def test_cdc_format(self):
        """Testar formato do CDC gerado"""
        from odoo.addons.l10n_py_edi_core.services.cdc_generator import CDCGenerator

        cdc = CDCGenerator.generate(
            company_ruc="12345678",
            doc_type=1,
            establishment="001",
            expedition_point="001",
            sequence=1,
            emission_date=datetime(2025, 1, 15, 10, 30),
        )

        # CDC deve ter 43 dígitos
        self.assertEqual(len(cdc), 43, f"CDC deve ter 43 dígitos, gerado: {len(cdc)}")

        # CDC deve conter apenas números
        self.assertTrue(cdc.isdigit(), "CDC deve conter apenas números")

    def test_cdc_structure(self):
        """Testar estrutura do CDC"""
        from odoo.addons.l10n_py_edi_core.services.cdc_generator import CDCGenerator

        cdc = CDCGenerator.generate(
            company_ruc="80012345",
            doc_type=1,
            establishment="001",
            expedition_point="002",
            sequence=123,
            emission_date=datetime(2025, 1, 15, 10, 30),
        )

        # Verificar componentes do CDC
        self.assertEqual(cdc[:8], "80012345", "RUC incorreto no CDC")
        self.assertEqual(cdc[8:10], "01", "Tipo documento incorreto no CDC")
        self.assertEqual(cdc[10:13], "001", "Estabelecimento incorreto no CDC")
        self.assertEqual(cdc[13:16], "002", "Ponto expedição incorreto no CDC")
        self.assertEqual(cdc[16:23], "0000123", "Sequência incorreta no CDC")

    def test_cdc_uniqueness(self):
        """Testar unicidade do CDC"""
        from odoo.addons.l10n_py_edi_core.services.cdc_generator import CDCGenerator

        # Gerar múltiplos CDCs com parâmetros similares
        cdcs = []
        for i in range(10):
            cdc = CDCGenerator.generate(
                company_ruc="12345678",
                doc_type=1,
                establishment="001",
                expedition_point="001",
                sequence=i + 1,
                emission_date=datetime.now(),
            )
            cdcs.append(cdc)

        # Todos devem ser únicos
        unique_cdcs = set(cdcs)
        self.assertEqual(len(cdcs), len(unique_cdcs), "CDCs devem ser únicos")

    def test_cdc_validation(self):
        """Testar validação de CDC"""
        from odoo.addons.l10n_py_edi_core.services.cdc_generator import CDCGenerator

        # CDC válido
        valid_cdc = CDCGenerator.generate(
            company_ruc="12345678",
            doc_type=1,
            establishment="001",
            expedition_point="001",
            sequence=1,
        )

        is_valid, error = CDCGenerator.validate_cdc(valid_cdc)
        self.assertTrue(is_valid, f"CDC válido foi rejeitado: {error}")

        # CDC inválido - comprimento
        is_valid, error = CDCGenerator.validate_cdc("123456789")
        self.assertFalse(is_valid, "CDC com comprimento incorreto deve ser inválido")

        # CDC inválido - dígito verificador
        invalid_cdc = valid_cdc[:-1] + "0"  # Trocar último dígito
        is_valid, error = CDCGenerator.validate_cdc(invalid_cdc)
        self.assertFalse(is_valid, "CDC com DV incorreto deve ser inválido")


# =============================================================================
# TESTES DE FATURAÇÃO
# =============================================================================


@tagged("post_install", "-at_install", "l10n_py", "invoice")
class TestInvoicing(TestL10nPyBase):
    """Testes para faturação paraguaia"""

    def test_invoice_creation(self):
        """Testar criação de fatura básica"""
        # Criar cliente
        partner = self.env["res.partner"].create(
            {
                "name": "Cliente Test",
                "l10n_py_ruc": "87654321-0",
                "l10n_py_taxpayer_type": "2",
            }
        )

        # Criar fatura
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.journal_sales.id,
                "invoice_date": date.today(),
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_gravado.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        self.assertTrue(invoice.id, "Fatura deve ser criada")
        self.assertEqual(
            invoice.l10n_py_edi_document_type,
            "1",
            "Tipo de documento deve ser Factura Electrónica",
        )

    def test_invoice_iva_calculation(self):
        """Testar cálculo de IVA por alíquota"""
        partner = self.env["res.partner"].create(
            {
                "name": "Cliente Test IVA",
                "l10n_py_ruc": "11111111-1",
                "l10n_py_taxpayer_type": "2",
            }
        )

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.journal_sales.id,
                "invoice_date": date.today(),
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_gravado.id,
                            "quantity": 1,
                            "price_unit": 100.0,  # IVA 10%
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_reducido.id,
                            "quantity": 1,
                            "price_unit": 50.0,  # IVA 5%
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_exento.id,
                            "quantity": 1,
                            "price_unit": 25.0,  # Exento
                        },
                    ),
                ],
            }
        )

        # Calcular impostos
        invoice._compute_tax_totals()

        # Verificar totais por alíquota
        self.assertAlmostEqual(invoice.amount_subtotal_10, 100.0, places=2)
        self.assertAlmostEqual(invoice.amount_iva_10, 10.0, places=2)
        self.assertAlmostEqual(invoice.amount_subtotal_5, 50.0, places=2)
        self.assertAlmostEqual(invoice.amount_iva_5, 2.5, places=2)
        self.assertAlmostEqual(invoice.amount_subtotal_exempt, 25.0, places=2)
        self.assertAlmostEqual(invoice.amount_iva_total, 12.5, places=2)

    def test_invoice_number_format(self):
        """Testar formato do número da fatura"""
        partner = self.env["res.partner"].create(
            {
                "name": "Cliente Test Number",
                "l10n_py_ruc": "22222222-2",
                "l10n_py_taxpayer_type": "2",
            }
        )

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.journal_sales.id,
                "invoice_date": date.today(),
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_gravado.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        invoice.action_post()

        # Verificar formato do número (001-001-0000001)
        number_pattern = r"^\d{3}-\d{3}-\d{7}$"
        self.assertTrue(
            re.match(number_pattern, invoice.full_invoice_number),
            f"Formato de número inválido: {invoice.full_invoice_number}",
        )

    def test_authorization_validation(self):
        """Testar validação de autorização"""
        partner = self.env["res.partner"].create(
            {
                "name": "Cliente Test Auth",
                "l10n_py_ruc": "33333333-3",
                "l10n_py_taxpayer_type": "2",
            }
        )

        # Criar autorização vencida
        expired_auth = self.env["account.authorization"].create(
            {
                "name": "87654321",
                "date_from": date.today() - timedelta(days=60),
                "date_to": date.today() - timedelta(days=30),  # Vencida
                "invoice_number_from": 1,
                "invoice_number_to": 1000,
                "establishment": "001",
                "expedition_point": "001",
                "document_type": "invoice",
                "company_id": self.company.id,
            }
        )

        # Tentar criar fatura com autorização vencida
        with self.assertRaises(ValidationError):
            invoice = self.env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": partner.id,
                    "journal_id": self.journal_sales.id,
                    "invoice_date": date.today(),
                    "authorization_id": expired_auth.id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product_gravado.id,
                                "quantity": 1,
                                "price_unit": 100.0,
                            },
                        )
                    ],
                }
            )
            invoice.action_post()


# =============================================================================
# TESTES DE EDI
# =============================================================================


@tagged("post_install", "-at_install", "l10n_py", "edi")
class TestEDIIntegration(TestL10nPyBase):
    """Testes para integração EDI"""

    def test_edi_document_type_computation(self):
        """Testar determinação automática do tipo de documento EDI"""
        partner = self.env["res.partner"].create(
            {
                "name": "Cliente EDI Test",
                "l10n_py_ruc": "44444444-4",
                "l10n_py_taxpayer_type": "2",
            }
        )

        # Fatura de venda
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.journal_sales.id,
            }
        )
        self.assertEqual(invoice.l10n_py_edi_document_type, "1")

        # Nota de crédito
        credit_note = self.env["account.move"].create(
            {
                "move_type": "out_refund",
                "partner_id": partner.id,
                "journal_id": self.journal_sales.id,
            }
        )
        self.assertEqual(credit_note.l10n_py_edi_document_type, "5")

    def test_cdc_generation_on_invoice(self):
        """Testar geração de CDC na fatura"""
        partner = self.env["res.partner"].create(
            {
                "name": "Cliente CDC Test",
                "l10n_py_ruc": "55555555-5",
                "l10n_py_taxpayer_type": "2",
            }
        )

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.journal_sales.id,
                "invoice_date": date.today(),
                "authorization_id": self.authorization.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_gravado.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        # Gerar CDC
        cdc = invoice._generate_cdc()

        self.assertTrue(cdc, "CDC deve ser gerado")
        self.assertEqual(len(cdc), 43, "CDC deve ter 43 dígitos")
        self.assertEqual(invoice.l10n_py_cdc, cdc, "CDC deve ser salvo na fatura")

    @unittest.skipIf(True, "Teste de integração - requer credenciais reais")
    def test_facturasend_connection(self):
        """Testar conexão com FacturaSend (ambiente de teste)"""
        # Este teste só deve rodar com credenciais reais configuradas
        connector = self.env["l10n_py.edi.connector.facturasend"].create(
            {
                "name": "Test Connector",
                "api_key": "test_api_key",
                "tenant_id": "test_tenant",
                "environment": "test",
            }
        )

        result = connector.test_connection()
        self.assertTrue(
            result.get("success", False),
            f"Falha na conexão: {result.get('error', 'Unknown')}",
        )


# =============================================================================
# TESTES DE LOGGING
# =============================================================================


@tagged("post_install", "-at_install", "l10n_py", "logging")
class TestEDILogging(TestL10nPyBase):
    """Testes para sistema de logs EDI"""

    def test_log_creation(self):
        """Testar criação de logs EDI"""
        partner = self.env["res.partner"].create(
            {
                "name": "Cliente Log Test",
                "l10n_py_ruc": "66666666-6",
                "l10n_py_taxpayer_type": "2",
            }
        )

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.journal_sales.id,
                "invoice_date": date.today(),
                "l10n_py_cdc": "1234567890123456789012345678901234567890123",
            }
        )

        # Criar log
        log = self.env["l10n_py.edi.log"].log_operation(
            operation_type="send",
            provider="factpy",
            document=invoice,
            request_data={"test": "data"},
            response_data={"status": "ok"},
            execution_time=150.5,
            success=True,
        )

        self.assertTrue(log, "Log deve ser criado")
        self.assertEqual(log.operation_type, "send")
        self.assertEqual(log.provider, "factpy")
        self.assertEqual(log.document_id, invoice)
        self.assertEqual(log.cdc, invoice.l10n_py_cdc)
        self.assertTrue(log.success)

    def test_log_error_handling(self):
        """Testar registro de erros no log"""
        log = self.env["l10n_py.edi.log"].log_operation(
            operation_type="send",
            provider="facturasend",
            success=False,
            error_message="Timeout na conexão",
            status_code=500,
        )

        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "Timeout na conexão")
        self.assertEqual(log.status_code, 500)


# =============================================================================
# TESTES DE PERFORMANCE
# =============================================================================


@tagged("post_install", "-at_install", "l10n_py", "performance")
class TestPerformance(TestL10nPyBase):
    """Testes de performance"""

    def test_bulk_ruc_validation(self):
        """Testar validação de RUC em lote"""
        import time

        start_time = time.time()

        # Criar 100 parceiros com RUC
        partners_data = []
        for i in range(100):
            partners_data.append(
                {
                    "name": f"Partner {i: 03d}",
                    "l10n_py_ruc": f"{1000000 + i: 07d}-{(i % 10)}",
                    "l10n_py_taxpayer_type": "2",
                }
            )

        partners = self.env["res.partner"].create(partners_data)

        execution_time = time.time() - start_time

        self.assertEqual(len(partners), 100, "Todos os parceiros devem ser criados")
        self.assertLess(
            execution_time,
            5.0,
            f"Validação de 100 RUCs deve ser rápida (atual: {execution_time: .2f}s)",
        )

    def test_bulk_cdc_generation(self):
        """Testar geração de CDC em lote"""
        import time

        from odoo.addons.l10n_py_edi_core.services.cdc_generator import CDCGenerator

        start_time = time.time()

        # Gerar 50 CDCs
        cdcs = []
        for i in range(50):
            cdc = CDCGenerator.generate(
                company_ruc="12345678",
                doc_type=1,
                establishment="001",
                expedition_point="001",
                sequence=i + 1,
            )
            cdcs.append(cdc)

        execution_time = time.time() - start_time

        self.assertEqual(len(cdcs), 50, "Todos os CDCs devem ser gerados")
        self.assertEqual(len(set(cdcs)), 50, "Todos os CDCs devem ser únicos")
        self.assertLess(
            execution_time,
            2.0,
            f"Geração de 50 CDCs deve ser rápida (atual: {execution_time: .2f}s)",
        )


# =============================================================================
# SUITE DE TESTES COMPLETA
# =============================================================================


def suite():
    """Criar suite completa de testes"""
    test_suite = unittest.TestSuite()

    # Testes unitários
    test_suite.addTest(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestRUCValidation)
    )
    test_suite.addTest(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestCDCGeneration)
    )

    # Testes de integração
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestInvoicing))
    test_suite.addTest(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestEDIIntegration)
    )
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestEDILogging))

    # Testes de performance
    test_suite.addTest(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestPerformance)
    )

    return test_suite


if __name__ == "__main__":
    # Executar todos os testes
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())

# =============================================================================
# COMANDOS PARA EXECUTAR TESTES
# =============================================================================

# Executar todos os testes da localização paraguaia
# python -m odoo.tests.loader -i l10n_py_core,l10n_py_accounting,l10n_py_edi_core --test-tags=l10n_py

# Executar apenas testes de RUC
# python -m odoo.tests.loader -i l10n_py_core --test-tags=ruc

# Executar apenas testes de CDC
# python -m odoo.tests.loader -i l10n_py_edi_core --test-tags=cdc

# Executar testes de performance
# python -m odoo.tests.loader -i l10n_py_core,l10n_py_edi_core --test-tags=performance

# Executar testes de EDI (sem integração real)
# python -m odoo.tests.loader -i l10n_py_edi_core --test-tags=edi,-integration

# Coverage report (com coverage.py instalado)
# coverage run --source=addons/l10n_py_core,addons/l10n_py_edi_core -m odoo.tests.loader -i l10n_py_core,l10n_py_edi_core --test-tags=l10n_py
# coverage html

# =============================================================================
# CONFIGURAÇÃO DE CI/CD
# =============================================================================

"""
# .github/workflows/tests.yml

name: L10n PY Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install coverage

    - name: Run tests
      env:
        DB_HOST: localhost
        DB_USER: postgres
        DB_PASSWORD: postgres
      run: |
        coverage run --source=addons/l10n_py_core,addons/l10n_py_edi_core -m odoo.tests.loader -i l10n_py_core,l10n_py_edi_core --test-tags=l10n_py

    - name: Generate coverage report
      run: |
        coverage xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
"""
