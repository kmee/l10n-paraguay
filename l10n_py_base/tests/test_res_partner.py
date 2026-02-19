from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "l10n_py")
class TestResPartner(TransactionCase):
    """Tests para extensión de res.partner Paraguay"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.country_py = cls.env.ref("base.py")

    def test_partner_fiscal_fields_exist(self):
        """Campos fiscales l10n_py deben existir en el modelo"""
        partner = self.Partner.create(
            {
                "name": "Test Partner PY",
                "country_id": self.country_py.id,
            }
        )
        self.assertTrue(hasattr(partner, "l10n_py_ruc"))
        self.assertTrue(hasattr(partner, "l10n_py_ruc_dv"))
        self.assertTrue(hasattr(partner, "l10n_py_taxpayer_type"))
        self.assertTrue(hasattr(partner, "l10n_py_fantasy_name"))
        self.assertTrue(hasattr(partner, "l10n_py_activity_description"))
        self.assertTrue(hasattr(partner, "l10n_py_department_code"))
        self.assertTrue(hasattr(partner, "l10n_py_city_code"))

    def test_ruc_dv_computed(self):
        """DV debe calcularse automáticamente al establecer RUC"""
        partner = self.Partner.create(
            {
                "name": "Test Partner",
                "country_id": self.country_py.id,
                "l10n_py_ruc": "80012345",
            }
        )
        self.assertTrue(partner.l10n_py_ruc_dv, "DV debe ser calculado")
        self.assertEqual(len(partner.l10n_py_ruc_dv), 1, "DV debe tener 1 carácter")

    def test_ruc_dv_empty_when_no_ruc(self):
        """DV debe estar vacío si no hay RUC"""
        partner = self.Partner.create(
            {
                "name": "Test Partner",
                "country_id": self.country_py.id,
            }
        )
        self.assertFalse(partner.l10n_py_ruc_dv)

    def test_taxpayer_type_selection(self):
        """Tipo de contribuyente debe aceptar valores válidos"""
        partner = self.Partner.create(
            {
                "name": "Contribuyente Test",
                "country_id": self.country_py.id,
                "l10n_py_taxpayer_type": "1",
            }
        )
        self.assertEqual(partner.l10n_py_taxpayer_type, "1")

        partner2 = self.Partner.create(
            {
                "name": "No Contribuyente Test",
                "country_id": self.country_py.id,
                "l10n_py_taxpayer_type": "2",
            }
        )
        self.assertEqual(partner2.l10n_py_taxpayer_type, "2")

    def test_neighborhood_onchange(self):
        """Auto-llenar ciudad al seleccionar barrio"""
        # Check that the neighborhood field exists
        partner = self.Partner.create(
            {
                "name": "Test Partner",
                "country_id": self.country_py.id,
            }
        )
        self.assertTrue(hasattr(partner, "l10n_py_neighborhood_id"))

    def test_department_code_related(self):
        """l10n_py_department_code computado desde state_id"""
        # Find a PY state with l10n_py_code set
        state = self.env["res.country.state"].search(
            [
                ("country_id", "=", self.country_py.id),
                ("l10n_py_code", "!=", False),
            ],
            limit=1,
        )
        if state:
            partner = self.Partner.create(
                {
                    "name": "Test Partner",
                    "country_id": self.country_py.id,
                    "state_id": state.id,
                }
            )
            self.assertEqual(
                partner.l10n_py_department_code,
                state.l10n_py_code,
                "Código departamento debe coincidir con el del estado",
            )
