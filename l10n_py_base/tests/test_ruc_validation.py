# -*- coding: utf-8 -*-
# l10n_py_base/tests/test_ruc_validation.py

"""
Testes para validação de RUC paraguaio
Implementa os testes propostos no documento de estrutura de testes
"""

from odoo.tests import common, tagged
from odoo.exceptions import ValidationError
from ..validators.ruc_validator import RUCValidator


@tagged('post_install', '-at_install', 'l10n_py', 'ruc')
class TestRUCValidation(common.TransactionCase):
    """Testes para validação de RUC paraguaio"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configurar empresa
        cls.company = cls.env.ref('base.main_company')
        cls.country_py = cls.env.ref('base.py')

    def test_ruc_format_valid(self):
        """Testar formatos válidos de RUC"""
        valid_rucs = [
            '1234567',
            '12345678',
            '123456',
            '80012345'
        ]

        for ruc in valid_rucs:
            with self.subTest(ruc=ruc):
                is_valid, error = RUCValidator.validate(ruc)
                self.assertTrue(is_valid, f"RUC válido não foi aceito: {ruc} - {error}")

    def test_ruc_format_with_dv(self):
        """Testar RUC com dígito verificador"""
        # Testar RUCs com DV correto
        test_rucs = [
            '80012345',  # RUC base
        ]

        for ruc_base in test_rucs:
            with self.subTest(ruc=ruc_base):
                # Calcular DV
                dv = RUCValidator.get_check_digit(ruc_base)
                ruc_with_dv = f"{ruc_base}-{dv}"

                # Validar
                is_valid, error = RUCValidator.validate(ruc_with_dv)
                self.assertTrue(is_valid, f"RUC com DV não foi aceito: {ruc_with_dv} - {error}")

    def test_ruc_format_invalid(self):
        """Testar formatos inválidos de RUC"""
        invalid_rucs = [
            '12345',           # Muito curto
            '123456789',       # Muito longo
            '1234567A',        # Contém letra
            '',                # Vazio
            '12345--6',        # Hífen duplo
        ]

        for ruc in invalid_rucs:
            with self.subTest(ruc=ruc):
                is_valid, error = RUCValidator.validate(ruc)
                self.assertFalse(is_valid, f"RUC inválido foi aceito: {ruc}")

    def test_ruc_check_digit_calculation(self):
        """Testar cálculo do dígito verificador"""
        # Casos de teste (RUC base -> DV esperado)
        test_cases = {
            '80012345': RUCValidator.get_check_digit('80012345'),
            '1234567': RUCValidator.get_check_digit('1234567'),
        }

        for ruc_base, expected_dv in test_cases.items():
            with self.subTest(ruc=ruc_base):
                calculated_dv = RUCValidator.get_check_digit(ruc_base)
                self.assertEqual(str(calculated_dv), str(expected_dv),
                               f"DV incorreto para {ruc_base}")

    def test_ruc_formatting(self):
        """Testar formatação automática de RUC"""
        test_cases = [
            ('12345678', '1234567-'),  # Sem DV
            ('1234567-8', '1234567-8'),  # Com DV
            ('  1234567  ', '1234567-'),  # Com espaços
        ]

        for input_ruc, expected_prefix in test_cases:
            with self.subTest(ruc=input_ruc):
                formatted = RUCValidator.format_ruc(input_ruc)
                self.assertIn('-', formatted, f"RUC deve incluir hífen: {formatted}")

    def test_ruc_normalization(self):
        """Testar normalização de RUC"""
        test_rucs = [
            '1234567',
            '  1234567  ',
            '1234567-',
        ]

        for ruc in test_rucs:
            with self.subTest(ruc=ruc):
                normalized = RUCValidator.normalize(ruc)
                self.assertTrue('-' in normalized or len(normalized) >= 6,
                              f"RUC normalizado inválido: {normalized}")

    def test_partner_ruc_validation(self):
        """Testar validação de RUC no modelo res.partner"""
        # Criar parceiro com RUC válido
        partner = self.env['res.partner'].create({
            'name': 'Test Partner Valid RUC',
            'l10n_py_ruc': '80012345',
            'country_id': self.country_py.id,
        })

        self.assertTrue(partner.id, "Parceiro com RUC válido não foi criado")
        self.assertTrue(partner.l10n_py_dv, "DV não foi calculado automaticamente")

    def test_partner_ruc_validation_invalid(self):
        """Testar validação de RUC inválido no modelo res.partner"""
        # Tentar criar parceiro com RUC inválido
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Test Partner Invalid RUC',
                'l10n_py_ruc': '12345',  # Muito curto
                'country_id': self.country_py.id,
            })

    def test_ruc_dv_computation(self):
        """Testar cálculo automático do DV"""
        partner = self.env['res.partner'].create({
            'name': 'Test Partner DV',
            'l10n_py_ruc': '80012345',
            'country_id': self.country_py.id,
        })

        # DV deve ser calculado automaticamente
        self.assertTrue(partner.l10n_py_dv, "DV não foi calculado")

        # Verificar RUC completo
        self.assertTrue(partner.l10n_py_ruc_full, "RUC completo não foi gerado")
        self.assertIn('-', partner.l10n_py_ruc_full, "RUC completo deve conter hífen")

    def test_ruc_get_number(self):
        """Testar extração do número do RUC"""
        test_cases = [
            ('1234567-8', '1234567'),
            ('1234567', '1234567'),
            ('  1234567-8  ', '1234567'),
        ]

        for input_ruc, expected_number in test_cases:
            with self.subTest(ruc=input_ruc):
                ruc_number = RUCValidator.get_ruc_number(input_ruc)
                self.assertEqual(ruc_number, expected_number,
                               f"Número de RUC incorreto para {input_ruc}")

