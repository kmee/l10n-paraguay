# -*- coding: utf-8 -*-
# l10n_py_edi_base/tests/test_cdc_generation.py

"""
Testes para geração de CDC (Código de Control)
Implementa os testes propostos no documento de estrutura de testes
"""

from odoo.tests import common, tagged
from odoo.exceptions import ValidationError
from datetime import datetime
from ..services.cdc_generator import CDCGenerator


@tagged('post_install', '-at_install', 'l10n_py', 'cdc')
class TestCDCGeneration(common.TransactionCase):
    """Testes para geração de CDC (Código de Control)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Dados de teste
        cls.company_ruc = '80012345'
        cls.doc_type = 1  # Factura Electrónica
        cls.establishment = '001'
        cls.expedition_point = '001'
        cls.sequence = 1
        cls.emission_date = datetime(2025, 1, 15, 10, 30)

    def test_cdc_format(self):
        """Testar formato do CDC gerado"""
        cdc = CDCGenerator.generate(
            company_ruc=self.company_ruc,
            doc_type=self.doc_type,
            establishment=self.establishment,
            expedition_point=self.expedition_point,
            sequence=self.sequence,
            emission_date=self.emission_date
        )

        # CDC deve ter 43 dígitos
        self.assertEqual(len(cdc), 43, f"CDC deve ter 43 dígitos, gerado: {len(cdc)}")

        # CDC deve conter apenas números
        self.assertTrue(cdc.isdigit(), "CDC deve conter apenas números")

    def test_cdc_structure(self):
        """Testar estrutura do CDC"""
        cdc = CDCGenerator.generate(
            company_ruc=self.company_ruc,
            doc_type=self.doc_type,
            establishment=self.establishment,
            expedition_point=self.expedition_point,
            sequence=self.sequence,
            emission_date=self.emission_date
        )

        # Parsear componentes
        components = CDCGenerator.parse_cdc(cdc)

        # Verificar componentes
        self.assertEqual(components['ruc'], self.company_ruc.zfill(8),
                        "RUC incorreto no CDC")
        self.assertEqual(components['doc_type'], f"{self.doc_type:02d}",
                        "Tipo documento incorreto no CDC")
        self.assertEqual(components['establishment'], self.establishment,
                        "Estabelecimento incorreto no CDC")
        self.assertEqual(components['expedition_point'], self.expedition_point,
                        "Ponto expedição incorreto no CDC")
        self.assertEqual(components['sequence'], f"{self.sequence:07d}",
                        "Sequência incorreta no CDC")

    def test_cdc_uniqueness(self):
        """Testar unicidade do CDC"""
        # Gerar múltiplos CDCs com parâmetros similares
        cdcs = []
        for i in range(10):
            cdc = CDCGenerator.generate(
                company_ruc=self.company_ruc,
                doc_type=self.doc_type,
                establishment=self.establishment,
                expedition_point=self.expedition_point,
                sequence=i + 1,
                emission_date=self.emission_date
            )
            cdcs.append(cdc)

        # Todos devem ser únicos
        unique_cdcs = set(cdcs)
        self.assertEqual(len(cdcs), len(unique_cdcs), "CDCs devem ser únicos")

    def test_cdc_validation(self):
        """Testar validação de CDC"""
        # Gerar CDC válido
        valid_cdc = CDCGenerator.generate(
            company_ruc=self.company_ruc,
            doc_type=self.doc_type,
            establishment=self.establishment,
            expedition_point=self.expedition_point,
            sequence=self.sequence,
            emission_date=self.emission_date
        )

        # Validar CDC
        is_valid, error = CDCGenerator.validate_cdc(valid_cdc)
        self.assertTrue(is_valid, f"CDC válido foi rejeitado: {error}")

    def test_cdc_validation_invalid_length(self):
        """Testar validação de CDC com comprimento incorreto"""
        # CDC inválido - comprimento
        is_valid, error = CDCGenerator.validate_cdc('123456789')
        self.assertFalse(is_valid, "CDC com comprimento incorreto deve ser inválido")
        self.assertIn('43 dígitos', error, "Mensagem de erro deve mencionar 43 dígitos")

    def test_cdc_validation_invalid_check_digit(self):
        """Testar validação de CDC com dígito verificador incorreto"""
        # Gerar CDC válido
        valid_cdc = CDCGenerator.generate(
            company_ruc=self.company_ruc,
            doc_type=self.doc_type,
            establishment=self.establishment,
            expedition_point=self.expedition_point,
            sequence=self.sequence,
            emission_date=self.emission_date
        )

        # Trocar último dígito (DV)
        invalid_cdc = valid_cdc[:-1] + '0' if valid_cdc[-1] != '0' else valid_cdc[:-1] + '1'

        # Validar
        is_valid, error = CDCGenerator.validate_cdc(invalid_cdc)
        self.assertFalse(is_valid, "CDC com DV incorreto deve ser inválido")
        self.assertIn('verificador inválido', error, "Mensagem deve indicar DV inválido")

    def test_cdc_validation_non_numeric(self):
        """Testar validação de CDC com caracteres não numéricos"""
        # CDC com letras
        invalid_cdc = 'A' * 43

        # Validar
        is_valid, error = CDCGenerator.validate_cdc(invalid_cdc)
        self.assertFalse(is_valid, "CDC com letras deve ser inválido")
        self.assertIn('números', error, "Mensagem deve mencionar que CDC deve conter números")

    def test_cdc_parse(self):
        """Testar parsing de CDC"""
        cdc = CDCGenerator.generate(
            company_ruc=self.company_ruc,
            doc_type=self.doc_type,
            establishment=self.establishment,
            expedition_point=self.expedition_point,
            sequence=self.sequence,
            emission_date=self.emission_date
        )

        # Parsear
        components = CDCGenerator.parse_cdc(cdc)

        # Verificar que todos os componentes estão presentes
        required_keys = ['ruc', 'doc_type', 'establishment', 'expedition_point',
                        'sequence', 'security_code', 'datetime_code', 'check_digit']

        for key in required_keys:
            self.assertIn(key, components, f"Componente {key} não encontrado")

    def test_cdc_format_display(self):
        """Testar formatação de CDC para exibição"""
        cdc = CDCGenerator.generate(
            company_ruc=self.company_ruc,
            doc_type=self.doc_type,
            establishment=self.establishment,
            expedition_point=self.expedition_point,
            sequence=self.sequence,
            emission_date=self.emission_date
        )

        # Formatar com separador padrão
        formatted = CDCGenerator.format_cdc(cdc)

        # Deve conter separadores
        self.assertIn('-', formatted, "CDC formatado deve conter separadores")

    def test_cdc_different_doc_types(self):
        """Testar geração de CDC para diferentes tipos de documentos"""
        doc_types = [1, 4, 5, 6, 7]  # FE, Autofactura, NC, ND, NR

        cdcs = []
        for doc_type in doc_types:
            cdc = CDCGenerator.generate(
                company_ruc=self.company_ruc,
                doc_type=doc_type,
                establishment=self.establishment,
                expedition_point=self.expedition_point,
                sequence=self.sequence,
                emission_date=self.emission_date
            )
            cdcs.append(cdc)

            # Verificar tipo de documento no CDC
            components = CDCGenerator.parse_cdc(cdc)
            self.assertEqual(components['doc_type'], f"{doc_type:02d}",
                           f"Tipo de documento incorreto para {doc_type}")

        # Todos devem ser únicos
        unique_cdcs = set(cdcs)
        self.assertEqual(len(cdcs), len(unique_cdcs),
                        "CDCs de diferentes tipos devem ser únicos")

    def test_cdc_invalid_parameters(self):
        """Testar geração de CDC com parâmetros inválidos"""
        # RUC inválido
        with self.assertRaises(ValueError):
            CDCGenerator.generate(
                company_ruc='12345',  # Muito curto
                doc_type=self.doc_type,
                establishment=self.establishment,
                expedition_point=self.expedition_point,
                sequence=self.sequence
            )

        # Tipo de documento inválido
        with self.assertRaises(ValueError):
            CDCGenerator.generate(
                company_ruc=self.company_ruc,
                doc_type=999,  # Inválido
                establishment=self.establishment,
                expedition_point=self.expedition_point,
                sequence=self.sequence
            )

        # Sequência inválida
        with self.assertRaises(ValueError):
            CDCGenerator.generate(
                company_ruc=self.company_ruc,
                doc_type=self.doc_type,
                establishment=self.establishment,
                expedition_point=self.expedition_point,
                sequence=99999999  # Muito grande
            )

