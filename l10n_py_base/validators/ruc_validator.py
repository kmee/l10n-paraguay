# l10n_py_base/validators/ruc_validator.py

"""
Validador robusto para RUC paraguaio
Implementa validação completa conforme especificações da SET
"""

import logging
import re

_logger = logging.getLogger(__name__)


class RUCValidator:
    """Validador robusto para RUC paraguaio"""

    # Multiplicadores para cálculo do dígito verificador (Módulo 11)
    MULTIPLIERS = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4]

    @classmethod
    def validate(cls, ruc):
        """
        Validação completa de RUC paraguaio

        Args:
            ruc (str): RUC a ser validado

        Returns:
            tuple: (is_valid, error_message)
        """
        if not ruc:
            return False, "RUC é obrigatório"

        # Limpar caracteres especiais
        clean_ruc = re.sub(r"[^\d-]", "", ruc)

        # Verificar formato básico (aceita com ou sem hífen)
        if not re.match(r"^\d{6,8}(-\d)?$", clean_ruc):
            return False, "Formato inválido. Use: XXXXXXX-D ou XXXXXXX"

        # Separar RUC e dígito verificador se houver hífen
        if "-" in clean_ruc:
            ruc_number, check_digit = clean_ruc.split("-")
        else:
            # Se não houver hífen, assume que o último dígito é o DV
            if len(clean_ruc) >= 7:
                ruc_number = clean_ruc[:-1]
                check_digit = clean_ruc[-1]
            else:
                ruc_number = clean_ruc
                check_digit = None

        # Validar comprimento
        if len(ruc_number) < 6 or len(ruc_number) > 8:
            return False, "RUC deve ter entre 6 e 8 dígitos"

        # Calcular dígito verificador esperado
        calculated_digit = cls._calculate_check_digit(ruc_number)

        # Se um DV foi fornecido, validá-lo
        if check_digit is not None:
            if str(calculated_digit) != check_digit:
                return (
                    False,
                    f"Dígito verificador inválido. "
                    f"Esperado: {calculated_digit}, "
                    f"Recebido: {check_digit}",
                )

        return True, ""

    @classmethod
    def _calculate_check_digit(cls, ruc_number):
        """
        Calcular dígito verificador usando módulo 11

        Args:
            ruc_number (str): Número do RUC sem dígito verificador

        Returns:
            int: Dígito verificador calculado
        """
        # Ajustar comprimento para 8 dígitos (padding com zeros à esquerda)
        ruc_padded = ruc_number.zfill(8)

        # Calcular soma ponderada
        total = 0
        for i, digit in enumerate(ruc_padded):
            total += int(digit) * cls.MULTIPLIERS[i]

        # Calcular resto da divisão por 11
        remainder = total % 11

        # Determinar dígito verificador
        if remainder < 2:
            return remainder
        else:
            return 11 - remainder

    @classmethod
    def format_ruc(cls, ruc, include_dv=True):
        """
        Formatar RUC para exibição padronizada

        Args:
            ruc (str): RUC a ser formatado
            include_dv (bool): Se True, inclui o dígito verificador

        Returns:
            str: RUC formatado (XXXXXXX-D)
        """
        # Limpar formato
        clean_ruc = re.sub(r"[^\d]", "", ruc)

        if len(clean_ruc) < 6:
            return ruc  # Retorna original se muito curto

        # Se o último dígito pode ser DV, separar
        if len(clean_ruc) >= 7:
            ruc_number = clean_ruc[:-1]
            existing_dv = clean_ruc[-1]

            # Validar se o DV está correto
            calculated_dv = cls._calculate_check_digit(ruc_number)

            if str(calculated_dv) == existing_dv:
                # DV correto, usar o fornecido
                if include_dv:
                    return f"{ruc_number}-{existing_dv}"
                else:
                    return ruc_number
            else:
                # DV incorreto ou não existe, calcular
                if include_dv:
                    new_dv = cls._calculate_check_digit(clean_ruc)
                    return f"{clean_ruc}-{new_dv}"
                else:
                    return clean_ruc
        else:
            # Sem DV, calcular
            if include_dv:
                dv = cls._calculate_check_digit(clean_ruc)
                return f"{clean_ruc}-{dv}"
            else:
                return clean_ruc

    @classmethod
    def get_ruc_number(cls, ruc):
        """
        Extrair apenas o número do RUC (sem DV)

        Args:
            ruc (str): RUC completo

        Returns:
            str: Número do RUC sem DV
        """
        clean_ruc = re.sub(r"[^\d]", "", ruc)

        if not clean_ruc:
            return ""

        # Se tiver DV (7-9 dígitos), remover último dígito
        if len(clean_ruc) >= 7:
            # Verificar se o último dígito é um DV válido
            ruc_number = clean_ruc[:-1]
            check_digit = clean_ruc[-1]
            calculated_digit = cls._calculate_check_digit(ruc_number)

            if str(calculated_digit) == check_digit:
                return ruc_number
            else:
                # Não é um DV válido, retornar completo
                return clean_ruc
        else:
            return clean_ruc

    @classmethod
    def get_check_digit(cls, ruc):
        """
        Obter o dígito verificador do RUC

        Args:
            ruc (str): RUC (com ou sem DV)

        Returns:
            str: Dígito verificador
        """
        ruc_number = cls.get_ruc_number(ruc)
        return str(cls._calculate_check_digit(ruc_number))

    @classmethod
    def is_valid_format(cls, ruc):
        """
        Verificar se o formato do RUC é válido (sem validar DV)

        Args:
            ruc (str): RUC a validar

        Returns:
            bool: True se o formato é válido
        """
        if not ruc:
            return False

        # RUC deve conter apenas dígitos e opcionalmente um hífen
        if not re.match(r"^[\d-]+$", ruc):
            return False

        clean_ruc = re.sub(r"[^\d]", "", ruc)

        # Deve ter entre 6 e 9 dígitos (6-8 para RUC + 1 para DV)
        if len(clean_ruc) < 6 or len(clean_ruc) > 9:
            return False

        return True

    @classmethod
    def normalize(cls, ruc):
        """
        Normalizar RUC para formato padronizado

        Args:
            ruc (str): RUC em qualquer formato

        Returns:
            str: RUC normalizado (XXXXXXX-D)
        """
        if not ruc:
            return ""

        is_valid, error = cls.validate(ruc)

        if not is_valid:
            _logger.warning(f"RUC inválido: {ruc} - {error}")
            return ruc  # Retorna original se inválido

        return cls.format_ruc(ruc, include_dv=True)
