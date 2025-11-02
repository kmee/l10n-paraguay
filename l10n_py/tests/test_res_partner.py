# -*- coding: utf-8 -*-
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install', 'l10n_py')
class TestResPartner(common.TransactionCase):
    """Testes para o modelo res.partner (extensão paraguaia)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.country_py = cls.env.ref('base.py')

    def test_01_create_partner_with_ruc(self):
        """Teste de criação de parceiro com RUC"""
        partner = self.Partner.create({
            'name': 'Test Partner',
            'ruc': '12345678-9',
            'taxpayer_type': 'juridica',
            'country_id': self.country_py.id,
        })

        self.assertTrue(partner.id, "Parceiro deve ser criado")
        self.assertEqual(partner.ruc, '12345678-9', "RUC deve estar salvo")

    def test_02_compute_ruc_dv(self):
        """Teste do cálculo do dígito verificador"""
        partner = self.Partner.create({
            'name': 'Test Partner',
            'ruc': '12345678-9',
            'taxpayer_type': 'juridica',
        })

        self.assertEqual(partner.ruc_dv, '9',
                        "Dígito verificador deve ser o último caractere")

    def test_03_validation_ruc_format_letters(self):
        """Teste de validação de RUC com letras"""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'Test Partner',
                'ruc': '1234567A-9',
                'taxpayer_type': 'juridica',
            })

    def test_04_validation_ruc_format_length_short(self):
        """Teste de validação de RUC muito curto"""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'Test Partner',
                'ruc': '12345-6',  # Muito curto
                'taxpayer_type': 'juridica',
            })

    def test_05_validation_ruc_format_length_long(self):
        """Teste de validação de RUC muito longo"""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'Test Partner',
                'ruc': '1234567890-1',  # Muito longo
                'taxpayer_type': 'juridica',
            })

    def test_06_validation_ruc_duplicate(self):
        """Teste de validação de RUC duplicado"""
        self.Partner.create({
            'name': 'First Partner',
            'ruc': '12345678-9',
            'taxpayer_type': 'juridica',
        })

        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'Second Partner',
                'ruc': '12345678-9',
                'taxpayer_type': 'juridica',
            })

    def test_07_format_ruc_method(self):
        """Teste do método de formatação de RUC"""
        partner = self.Partner.create({
            'name': 'Test Partner',
            'taxpayer_type': 'juridica',
        })

        # Testar formatação sem hífen
        formatted = partner._format_ruc('123456789')
        self.assertEqual(formatted, '12345678-9',
                        "RUC deve ser formatado com hífen")

        # Testar formatação já com hífen
        formatted = partner._format_ruc('12345678-9')
        self.assertEqual(formatted, '12345678-9',
                        "RUC já formatado deve permanecer igual")

    def test_08_onchange_ruc_formatting(self):
        """Teste da formatação automática no onchange"""
        partner = self.Partner.new({
            'name': 'Test Partner',
            'ruc': '123456789',
            'taxpayer_type': 'juridica',
        })

        partner._onchange_ruc()

        self.assertEqual(partner.ruc, '12345678-9',
                        "RUC deve ser formatado automaticamente")

    def test_09_name_get_with_ruc_company(self):
        """Teste do name_get para empresa com RUC"""
        partner = self.Partner.create({
            'name': 'Test Company',
            'is_company': True,
            'ruc': '12345678-9',
            'taxpayer_type': 'juridica',
        })

        name = partner.name_get()[0][1]
        self.assertIn('Test Company', name, "Nome deve aparecer")
        self.assertIn('12345678-9', name, "RUC deve aparecer no nome")

    def test_10_name_get_with_ruc_individual(self):
        """Teste do name_get para pessoa física com RUC"""
        partner = self.Partner.create({
            'name': 'Juan Pérez',
            'is_company': False,
            'ruc': '3456789-0',
            'taxpayer_type': 'natural',
        })

        name = partner.name_get()[0][1]
        self.assertIn('Juan Pérez', name, "Nome deve aparecer")
        self.assertIn('3456789-0', name, "RUC deve aparecer no nome")

    def test_11_name_get_without_ruc(self):
        """Teste do name_get sem RUC"""
        partner = self.Partner.create({
            'name': 'Test Partner',
            'taxpayer_type': 'foreign',
        })

        name = partner.name_get()[0][1]
        self.assertEqual(name, 'Test Partner', "Nome deve ser simples sem RUC")

    def test_12_name_search_by_name(self):
        """Teste de busca por nome"""
        partner = self.Partner.create({
            'name': 'Empresa Paraguaya',
            'ruc': '12345678-9',
            'taxpayer_type': 'juridica',
        })

        result = self.Partner.name_search('Paraguaya')
        partner_ids = [r[0] for r in result]

        self.assertIn(partner.id, partner_ids,
                     "Parceiro deve ser encontrado por nome")

    def test_13_name_search_by_ruc(self):
        """Teste de busca por RUC"""
        partner = self.Partner.create({
            'name': 'Empresa Test',
            'ruc': '98765432-1',
            'taxpayer_type': 'juridica',
        })

        result = self.Partner.name_search('98765432')
        partner_ids = [r[0] for r in result]

        self.assertIn(partner.id, partner_ids,
                     "Parceiro deve ser encontrado por RUC")

    def test_14_taxpayer_type_natural(self):
        """Teste de tipo de contribuinte - Pessoa Física"""
        partner = self.Partner.create({
            'name': 'María González',
            'ruc': '2345678-9',
            'taxpayer_type': 'natural',
        })

        self.assertEqual(partner.taxpayer_type, 'natural',
                        "Tipo deve ser pessoa física")

    def test_15_taxpayer_type_juridica(self):
        """Teste de tipo de contribuinte - Pessoa Jurídica"""
        partner = self.Partner.create({
            'name': 'Empresa S.A.',
            'ruc': '80012345-6',
            'taxpayer_type': 'juridica',
        })

        self.assertEqual(partner.taxpayer_type, 'juridica',
                        "Tipo deve ser pessoa jurídica")

    def test_16_taxpayer_type_foreign(self):
        """Teste de tipo de contribuinte - Extranjero"""
        partner = self.Partner.create({
            'name': 'Foreign Company',
            'taxpayer_type': 'foreign',
            'country_id': self.env.ref('base.br').id,
        })

        self.assertEqual(partner.taxpayer_type, 'foreign',
                        "Tipo deve ser extranjero")
        self.assertFalse(partner.ruc,
                        "Extranjero pode não ter RUC paraguaio")

    def test_17_ruc_with_dots_removed(self):
        """Teste de RUC com pontos (devem ser removidos)"""
        partner = self.Partner.create({
            'name': 'Test Partner',
            'ruc': '1.234.567-8',
            'taxpayer_type': 'juridica',
        })

        # A validação deve processar e aceitar
        self.assertTrue(partner.id, "Parceiro deve ser criado")

    def test_18_ruc_with_spaces_removed(self):
        """Teste de RUC com espaços (devem ser removidos)"""
        partner = self.Partner.create({
            'name': 'Test Partner',
            'ruc': '1 234 567-8',
            'taxpayer_type': 'juridica',
        })

        # A validação deve processar e aceitar
        self.assertTrue(partner.id, "Parceiro deve ser criado")

    def test_19_update_ruc_existing_partner(self):
        """Teste de atualização de RUC em parceiro existente"""
        partner = self.Partner.create({
            'name': 'Test Partner',
            'taxpayer_type': 'juridica',
        })

        partner.write({'ruc': '12345678-9'})

        self.assertEqual(partner.ruc, '12345678-9',
                        "RUC deve ser atualizado")

    def test_20_ruc_optional_field(self):
        """Teste de que RUC é opcional"""
        partner = self.Partner.create({
            'name': 'Test Partner Without RUC',
            'taxpayer_type': 'foreign',
        })

        self.assertTrue(partner.id, "Parceiro sem RUC deve ser criado")
        self.assertFalse(partner.ruc, "RUC deve estar vazio")

    def test_21_multiple_partners_different_rucs(self):
        """Teste de múltiplos parceiros com RUCs diferentes"""
        partner1 = self.Partner.create({
            'name': 'Partner 1',
            'ruc': '11111111-1',
            'taxpayer_type': 'juridica',
        })

        partner2 = self.Partner.create({
            'name': 'Partner 2',
            'ruc': '22222222-2',
            'taxpayer_type': 'juridica',
        })

        self.assertNotEqual(partner1.ruc, partner2.ruc,
                          "RUCs devem ser diferentes")
        self.assertTrue(partner1.id and partner2.id,
                       "Ambos parceiros devem ser criados")
