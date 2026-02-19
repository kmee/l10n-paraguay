from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "l10n_py")
class TestAccountAuthorization(TransactionCase):
    """Tests para el modelo account.authorization"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Authorization = cls.env["account.authorization"]
        cls.company = cls.env.ref("base.main_company")
        cls.country_py = cls.env.ref("base.py")

        # Obtener tipo de documento factura
        cls.doc_type_invoice = cls.env["l10n_latam.document.type"].search(
            [("country_id", "=", cls.country_py.id), ("code", "=", "1")],
            limit=1,
        )
        if not cls.doc_type_invoice:
            cls.doc_type_invoice = cls.env["l10n_latam.document.type"].create(
                {
                    "name": "Factura",
                    "code": "1",
                    "country_id": cls.country_py.id,
                    "internal_type": "invoice",
                }
            )

        cls.today = date.today()
        cls.date_from = cls.today - timedelta(days=30)
        cls.date_to = cls.today + timedelta(days=335)

    def _create_authorization(self, **kwargs):
        vals = {
            "name": "12345678",
            "date_from": self.date_from,
            "date_to": self.date_to,
            "invoice_number_from": 1,
            "invoice_number_to": 10000,
            "establishment": "001",
            "expedition_point": "001",
            "l10n_latam_document_type_id": self.doc_type_invoice.id,
            "company_id": self.company.id,
        }
        vals.update(kwargs)
        return self.Authorization.create(vals)

    def test_create_authorization(self):
        """Crear timbrado válido"""
        auth = self._create_authorization()
        self.assertTrue(auth.id)
        self.assertEqual(auth.state, "valid")

    def test_authorization_state_valid(self):
        """Estado 'valid' cuando vigente"""
        auth = self._create_authorization()
        self.assertEqual(auth.state, "valid")

    def test_authorization_state_expired(self):
        """Estado 'expired' cuando vencido"""
        auth = self._create_authorization(
            date_from=self.today - timedelta(days=400),
            date_to=self.today - timedelta(days=35),
        )
        self.assertEqual(auth.state, "expired")

    def test_authorization_state_to_expire(self):
        """Estado 'to_expire' cuando < 30 días"""
        auth = self._create_authorization(
            date_from=self.today - timedelta(days=300),
            date_to=self.today + timedelta(days=25),
        )
        self.assertEqual(auth.state, "to_expire")

    def test_timbrado_format_validation(self):
        """Rechaza timbrado con != 8 dígitos"""
        with self.assertRaises(ValidationError):
            self._create_authorization(name="1234567")  # 7 dígitos

        with self.assertRaises(ValidationError):
            self._create_authorization(name="1234567A")  # letras

    def test_establishment_format_validation(self):
        """Rechaza establecimiento con != 3 dígitos"""
        with self.assertRaises(ValidationError):
            self._create_authorization(establishment="01")

        with self.assertRaises(ValidationError):
            self._create_authorization(establishment="00A")

    def test_invoice_range_validation(self):
        """Rechaza range inválido (from > to)"""
        with self.assertRaises(ValidationError):
            self._create_authorization(invoice_number_from=1000, invoice_number_to=500)

    def test_date_validation(self):
        """Rechaza date_to < date_from"""
        with self.assertRaises(ValidationError):
            self._create_authorization(
                date_from=self.today,
                date_to=self.today - timedelta(days=1),
            )

    def test_document_type_latam_integration(self):
        """l10n_latam_document_type_id funciona"""
        auth = self._create_authorization()
        self.assertEqual(auth.l10n_latam_document_type_id, self.doc_type_invoice)

    def test_check_validity(self):
        """Verificación de vigencia"""
        auth = self._create_authorization()
        self.assertTrue(auth.check_validity())

    def test_check_validity_expired(self):
        """Timbrado vencido lanza error"""
        auth = self._create_authorization(
            date_from=self.today - timedelta(days=400),
            date_to=self.today - timedelta(days=35),
        )
        with self.assertRaises(ValidationError):
            auth.check_validity()

    def test_check_number_available(self):
        """Número dentro del range y no usado"""
        auth = self._create_authorization()
        self.assertTrue(auth.check_number_available(500))

    def test_check_number_out_of_range(self):
        """Número fuera del range"""
        auth = self._create_authorization()
        with self.assertRaises(ValidationError):
            auth.check_number_available(15000)

    def test_next_number_computation(self):
        """Próximo número correcto"""
        auth = self._create_authorization()
        self.assertEqual(auth.next_number, 1)

    def test_name_get(self):
        """Formato de visualización"""
        auth = self._create_authorization(
            expedition_point="002",
        )
        name = auth.name_get()[0][1]
        self.assertIn("12345678", name)
        self.assertIn("001-002", name)
