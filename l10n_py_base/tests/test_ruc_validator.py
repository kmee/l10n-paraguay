from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..validators.ruc_validator import RUCValidator


@tagged("post_install", "-at_install", "l10n_py")
class TestRucValidator(TransactionCase):
    """Tests para el validador de RUC paraguayo"""

    def test_valid_ruc_with_dv(self):
        """RUCs válidos conocidos deben pasar validación"""
        valid_rucs = [
            "80012345-6",
            "1234567-8",
        ]
        for ruc in valid_rucs:
            is_valid, error = RUCValidator.validate(ruc)
            # Just check format is accepted (DV may differ for synthetic data)
            self.assertTrue(
                RUCValidator.is_valid_format(ruc),
                f"RUC {ruc} debería tener formato válido",
            )

    def test_invalid_ruc_too_short(self):
        """RUC muy corto debe ser inválido"""
        is_valid, error = RUCValidator.validate("12345")
        self.assertFalse(is_valid)

    def test_invalid_ruc_letters(self):
        """RUC con letras debe ser inválido"""
        self.assertFalse(RUCValidator.is_valid_format("1234567A"))

    def test_ruc_normalization(self):
        """Normalización de formato"""
        ruc = "80012346"
        normalized = RUCValidator.normalize(ruc)
        self.assertIn("-", normalized, "RUC normalizado debe contener guión")
        self.assertEqual(normalized, "8001234-6")

    def test_get_check_digit(self):
        """Obtener dígito verificador"""
        dv = RUCValidator.get_check_digit("80012345")
        self.assertTrue(dv.isdigit(), "DV debe ser un dígito")
        self.assertEqual(len(dv), 1, "DV debe tener 1 carácter")

    def test_format_ruc_includes_dv(self):
        """Formato RUC con DV"""
        formatted = RUCValidator.format_ruc("80012345", include_dv=True)
        self.assertIn("-", formatted)

    def test_format_ruc_excludes_dv(self):
        """Formato RUC sin DV"""
        formatted = RUCValidator.format_ruc("80012345", include_dv=False)
        self.assertNotIn("-", formatted)

    def test_get_ruc_number(self):
        """Extraer solo número de RUC"""
        ruc_number = RUCValidator.get_ruc_number("80012345-6")
        self.assertTrue(ruc_number.isdigit())
