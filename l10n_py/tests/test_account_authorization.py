# -*- coding: utf-8 -*-
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError
from datetime import date, timedelta


@tagged('post_install', '-at_install', 'l10n_py')
class TestAccountAuthorization(common.TransactionCase):
    """Testes para o modelo account.authorization"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Authorization = cls.env['account.authorization']
        cls.company = cls.env.ref('base.main_company')

        # Datas para testes
        cls.today = date.today()
        cls.date_from = cls.today - timedelta(days=30)
        cls.date_to = cls.today + timedelta(days=335)

    def test_01_create_authorization_valid(self):
        """Teste de criação de timbrado válido"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
            'company_id': self.company.id,
        })

        self.assertTrue(authorization.id, "Timbrado deve ser criado")
        self.assertEqual(authorization.state, 'valid', "Timbrado deve estar vigente")
        self.assertTrue(authorization.active, "Timbrado deve estar ativo")

    def test_02_validation_timbrado_format(self):
        """Teste de validação do formato do número de timbrado"""
        # Timbrado com menos de 8 dígitos
        with self.assertRaises(ValidationError):
            self.Authorization.create({
                'name': '1234567',  # 7 dígitos
                'date_from': self.date_from,
                'date_to': self.date_to,
                'invoice_number_from': 1,
                'invoice_number_to': 10000,
                'establishment': '001',
                'expedition_point': '001',
                'document_type': 'invoice',
            })

        # Timbrado com letras
        with self.assertRaises(ValidationError):
            self.Authorization.create({
                'name': '1234567A',
                'date_from': self.date_from,
                'date_to': self.date_to,
                'invoice_number_from': 1,
                'invoice_number_to': 10000,
                'establishment': '001',
                'expedition_point': '001',
                'document_type': 'invoice',
            })

    def test_03_validation_establishment_format(self):
        """Teste de validação do formato do estabelecimento"""
        # Estabelecimento com formato inválido
        with self.assertRaises(ValidationError):
            self.Authorization.create({
                'name': '12345678',
                'date_from': self.date_from,
                'date_to': self.date_to,
                'invoice_number_from': 1,
                'invoice_number_to': 10000,
                'establishment': '01',  # Apenas 2 dígitos
                'expedition_point': '001',
                'document_type': 'invoice',
            })

        # Estabelecimento com letras
        with self.assertRaises(ValidationError):
            self.Authorization.create({
                'name': '12345678',
                'date_from': self.date_from,
                'date_to': self.date_to,
                'invoice_number_from': 1,
                'invoice_number_to': 10000,
                'establishment': '00A',
                'expedition_point': '001',
                'document_type': 'invoice',
            })

    def test_04_validation_expedition_point_format(self):
        """Teste de validação do formato do ponto de expedição"""
        with self.assertRaises(ValidationError):
            self.Authorization.create({
                'name': '12345678',
                'date_from': self.date_from,
                'date_to': self.date_to,
                'invoice_number_from': 1,
                'invoice_number_to': 10000,
                'establishment': '001',
                'expedition_point': '1',  # Apenas 1 dígito
                'document_type': 'invoice',
            })

    def test_05_validation_invoice_range(self):
        """Teste de validação do intervalo de numeração"""
        # Número final menor que inicial
        with self.assertRaises(ValidationError):
            self.Authorization.create({
                'name': '12345678',
                'date_from': self.date_from,
                'date_to': self.date_to,
                'invoice_number_from': 1000,
                'invoice_number_to': 500,
                'establishment': '001',
                'expedition_point': '001',
                'document_type': 'invoice',
            })

        # Número inicial zero ou negativo
        with self.assertRaises(ValidationError):
            self.Authorization.create({
                'name': '12345678',
                'date_from': self.date_from,
                'date_to': self.date_to,
                'invoice_number_from': 0,
                'invoice_number_to': 10000,
                'establishment': '001',
                'expedition_point': '001',
                'document_type': 'invoice',
            })

    def test_06_validation_dates(self):
        """Teste de validação de datas"""
        # Data final anterior à data inicial
        with self.assertRaises(ValidationError):
            self.Authorization.create({
                'name': '12345678',
                'date_from': self.today,
                'date_to': self.today - timedelta(days=1),
                'invoice_number_from': 1,
                'invoice_number_to': 10000,
                'establishment': '001',
                'expedition_point': '001',
                'document_type': 'invoice',
            })

    def test_07_compute_state_valid(self):
        """Teste do cálculo do estado - vigente"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.today - timedelta(days=30),
            'date_to': self.today + timedelta(days=335),
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
        })

        self.assertEqual(authorization.state, 'valid', "Timbrado deve estar vigente")

    def test_08_compute_state_to_expire(self):
        """Teste do cálculo do estado - por vencer"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.today - timedelta(days=300),
            'date_to': self.today + timedelta(days=25),
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
        })

        self.assertEqual(authorization.state, 'to_expire', "Timbrado deve estar por vencer")

    def test_09_compute_state_expired(self):
        """Teste do cálculo do estado - vencido"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.today - timedelta(days=400),
            'date_to': self.today - timedelta(days=35),
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
        })

        self.assertEqual(authorization.state, 'expired', "Timbrado deve estar vencido")

    def test_10_compute_next_number(self):
        """Teste do cálculo do próximo número"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
        })

        self.assertEqual(authorization.next_number, 1,
                        "Próximo número deve ser o primeiro do intervalo")

    def test_11_compute_remaining_numbers(self):
        """Teste do cálculo de números disponíveis"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
        })

        expected_numbers = 10000 - 1 + 1  # 10000 números
        self.assertEqual(authorization.remaining_numbers, expected_numbers,
                        "Deve ter 10000 números disponíveis")

    def test_12_check_validity_valid(self):
        """Teste de verificação de validade - timbrado válido"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.today - timedelta(days=30),
            'date_to': self.today + timedelta(days=335),
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
            'active': True,
        })

        # Não deve lançar exceção
        result = authorization.check_validity()
        self.assertTrue(result, "Verificação deve retornar True")

    def test_13_check_validity_inactive(self):
        """Teste de verificação de validade - timbrado inativo"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
            'active': False,
        })

        with self.assertRaises(ValidationError):
            authorization.check_validity()

    def test_14_check_validity_expired(self):
        """Teste de verificação de validade - timbrado vencido"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.today - timedelta(days=400),
            'date_to': self.today - timedelta(days=35),
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
        })

        with self.assertRaises(ValidationError):
            authorization.check_validity()

    def test_15_check_number_available(self):
        """Teste de verificação de número disponível"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '001',
            'document_type': 'invoice',
        })

        # Número dentro do intervalo
        result = authorization.check_number_available(500)
        self.assertTrue(result, "Número 500 deve estar disponível")

        # Número fora do intervalo
        with self.assertRaises(ValidationError):
            authorization.check_number_available(15000)

    def test_16_name_get(self):
        """Teste do formato de exibição do nome"""
        authorization = self.Authorization.create({
            'name': '12345678',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'invoice_number_from': 1,
            'invoice_number_to': 10000,
            'establishment': '001',
            'expedition_point': '002',
            'document_type': 'invoice',
        })

        name = authorization.name_get()[0][1]
        self.assertIn('12345678', name, "Nome deve conter o número do timbrado")
        self.assertIn('001-002', name, "Nome deve conter estabelecimento e ponto de expedição")
