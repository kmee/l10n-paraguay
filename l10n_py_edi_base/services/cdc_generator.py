# -*- coding: utf-8 -*-
# l10n_py_edi_base/services/cdc_generator.py

"""
Gerador de Código de Control (CDC) para documentos eletrônicos paraguaios
Implementação conforme Manual Técnico SIFEN v150
"""

import random
import hashlib
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class CDCGenerator:
    """
    Gerador de Código de Control (CDC) para documentos eletrônicos
    
    Formato CDC (43 dígitos):
    - RUC do emissor (8 dígitos)
    - Tipo de documento (2 dígitos)
    - Estabelecimento (3 dígitos)
    - Ponto de expedição (3 dígitos)
    - Número do documento (7 dígitos)
    - Código de segurança (8 dígitos)
    - Data/hora de emissão (11 dígitos)
    - Dígito verificador (1 dígito)
    """

    # Multiplicadores para dígito verificador (posições 1-42)
    MULTIPLIERS = [2, 3, 4, 5, 6, 7, 8, 9] * 6  # Repetir até 42 posições

    @classmethod
    def generate(cls, company_ruc, doc_type, establishment,
                 expedition_point, sequence, emission_date=None):
        """
        Gerar CDC conforme especificação SIFEN v150

        Args:
            company_ruc (str): RUC da empresa emissora (sem DV)
            doc_type (int): Tipo de documento (1=FE, 4=Autofactura, etc.)
            establishment (str): Establecimiento (3 dígitos)
            expedition_point (str): Punto de expedición (3 dígitos)
            sequence (int): Número sequencial do documento
            emission_date (datetime): Data de emissão (opcional)

        Returns:
            str: CDC completo com dígito verificador (43 dígitos)
        """
        if emission_date is None:
            emission_date = datetime.now()

        # Validar parâmetros
        cls._validate_parameters(
            company_ruc, doc_type, establishment,
            expedition_point, sequence
        )

        # Construir CDC base (42 dígitos)
        cdc_base = cls._build_cdc_base(
            company_ruc, doc_type, establishment,
            expedition_point, sequence, emission_date
        )

        # Calcular dígito verificador
        check_digit = cls._calculate_check_digit(cdc_base)

        # CDC final (43 dígitos)
        cdc_complete = cdc_base + str(check_digit)

        # Validar formato final
        if len(cdc_complete) != 43:
            raise ValueError(f"CDC deve ter 43 dígitos, gerado: {len(cdc_complete)}")

        _logger.info(f"CDC gerado: {cdc_complete}")
        return cdc_complete

    @classmethod
    def _validate_parameters(cls, company_ruc, doc_type, establishment,
                            expedition_point, sequence):
        """Validar parâmetros de entrada"""
        # Validar RUC
        ruc_clean = ''.join(filter(str.isdigit, str(company_ruc)))
        if len(ruc_clean) < 6 or len(ruc_clean) > 8:
            raise ValueError(f"RUC inválido: {company_ruc}")

        # Validar tipo de documento
        if not isinstance(doc_type, int) or doc_type < 1 or doc_type > 99:
            raise ValueError(f"Tipo de documento inválido: {doc_type}")

        # Validar establishment
        est_clean = str(establishment).zfill(3)
        if len(est_clean) != 3 or not est_clean.isdigit():
            raise ValueError(f"Establecimiento inválido: {establishment}")

        # Validar expedition point
        exp_clean = str(expedition_point).zfill(3)
        if len(exp_clean) != 3 or not exp_clean.isdigit():
            raise ValueError(f"Punto de expedición inválido: {expedition_point}")

        # Validar sequence
        if not isinstance(sequence, int) or sequence < 1 or sequence > 9999999:
            raise ValueError(f"Sequência inválida: {sequence}")

    @classmethod
    def _build_cdc_base(cls, company_ruc, doc_type, establishment,
                        expedition_point, sequence, emission_date):
        """
        Construir base do CDC (42 dígitos)

        Formato conforme SIFEN:
        - RUC: 8 dígitos
        - Tipo documento: 2 dígitos
        - Establecimiento: 3 dígitos
        - Punto expedición: 3 dígitos
        - Número documento: 7 dígitos
        - Código segurança: 8 dígitos
        - Data/hora: 11 dígitos (YYMMDDHHmm + random)
        """
        # RUC da empresa (8 dígitos - extrair apenas números)
        ruc_clean = ''.join(filter(str.isdigit, str(company_ruc)))
        cdc = ruc_clean[:8].zfill(8)

        # Tipo de documento (2 dígitos)
        cdc += f"{doc_type:02d}"

        # Establecimiento (3 dígitos)
        cdc += f"{int(establishment):03d}"

        # Punto de expedición (3 dígitos)
        cdc += f"{int(expedition_point):03d}"

        # Número do documento (7 dígitos)
        cdc += f"{sequence:07d}"

        # Código de segurança (8 dígitos) - gerado aleatoriamente
        security_code = cls._generate_security_code()
        cdc += f"{security_code:08d}"

        # Data e hora (11 dígitos)
        datetime_code = cls._generate_datetime_code(emission_date)
        cdc += datetime_code

        if len(cdc) != 42:
            raise ValueError(f"CDC base deve ter 42 dígitos, gerado: {len(cdc)}")

        return cdc

    @classmethod
    def _generate_security_code(cls):
        """Gerar código de segurança aleatório (8 dígitos)"""
        return random.randint(10000000, 99999999)

    @classmethod
    def _generate_datetime_code(cls, emission_date):
        """
        Gerar código de data/hora (11 dígitos)

        Formato: YYMMDDHHmm + dígito aleatório
        """
        date_str = emission_date.strftime("%y%m%d%H%M")  # 10 dígitos
        random_digit = random.randint(0, 9)  # 1 dígito

        return date_str + str(random_digit)

    @classmethod
    def _calculate_check_digit(cls, cdc_base):
        """
        Calcular dígito verificador usando módulo 11

        Args:
            cdc_base (str): CDC base (42 dígitos)

        Returns:
            int: Dígito verificador (0-9)
        """
        if len(cdc_base) != 42:
            raise ValueError(f"CDC base deve ter 42 dígitos, recebido: {len(cdc_base)}")

        # Calcular soma ponderada
        total = 0
        for i, digit in enumerate(cdc_base):
            multiplier = cls.MULTIPLIERS[i % len(cls.MULTIPLIERS)]
            total += int(digit) * multiplier

        # Calcular resto da divisão por 11
        remainder = total % 11

        # Determinar dígito verificador
        if remainder < 2:
            return remainder
        else:
            return 11 - remainder

    @classmethod
    def validate_cdc(cls, cdc):
        """
        Validar formato e dígito verificador de um CDC

        Args:
            cdc (str): CDC a ser validado

        Returns:
            tuple: (is_valid, error_message)
        """
        if not cdc:
            return False, "CDC é obrigatório"

        # Verificar comprimento
        if len(cdc) != 43:
            return False, f"CDC deve ter 43 dígitos, recebido: {len(cdc)}"

        # Verificar se contém apenas dígitos
        if not cdc.isdigit():
            return False, "CDC deve conter apenas números"

        # Separar base e dígito verificador
        cdc_base = cdc[:42]
        check_digit = int(cdc[42])

        # Calcular dígito verificador esperado
        try:
            calculated_digit = cls._calculate_check_digit(cdc_base)
        except Exception as e:
            return False, f"Erro ao calcular DV: {str(e)}"

        if calculated_digit != check_digit:
            return False, f"Dígito verificador inválido. Esperado: {calculated_digit}, Recebido: {check_digit}"

        return True, ""

    @classmethod
    def parse_cdc(cls, cdc):
        """
        Extrair componentes do CDC

        Args:
            cdc (str): CDC completo (43 dígitos)

        Returns:
            dict: Dicionário com componentes do CDC
        """
        if len(cdc) != 43:
            raise ValueError(f"CDC deve ter 43 dígitos, recebido: {len(cdc)}")

        return {
            'ruc': cdc[0:8],
            'doc_type': cdc[8:10],
            'establishment': cdc[10:13],
            'expedition_point': cdc[13:16],
            'sequence': cdc[16:23],
            'security_code': cdc[23:31],
            'datetime_code': cdc[31:42],
            'check_digit': cdc[42],
        }

    @classmethod
    def format_cdc(cls, cdc, separator='-'):
        """
        Formatar CDC para exibição legível

        Args:
            cdc (str): CDC completo
            separator (str): Separador entre componentes

        Returns:
            str: CDC formatado
        """
        if len(cdc) != 43:
            return cdc

        components = cls.parse_cdc(cdc)

        return (f"{components['ruc']}{separator}"
                f"{components['doc_type']}{separator}"
                f"{components['establishment']}{separator}"
                f"{components['expedition_point']}{separator}"
                f"{components['sequence']}{separator}"
                f"{components['security_code']}{separator}"
                f"{components['datetime_code']}{separator}"
                f"{components['check_digit']}")

