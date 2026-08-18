from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "l10n_py")
class TestResPartnerBank(TransactionCase):
    """Tests para los campos de beneficiario SIPAP en res.partner.bank."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PartnerBank = cls.env["res.partner.bank"]
        cls.partner = cls.env["res.partner"].create({"name": "SIPAP Test Partner"})

    def test_document_type_and_number_together_ok(self):
        """Tipo y número de documento completos juntos: no debe fallar."""
        bank_account = self.PartnerBank.create(
            {
                "acc_number": "SIPAP-DOC-OK",
                "partner_id": self.partner.id,
                "l10n_py_document_type": "ci",
                "l10n_py_document_number": "1234567",
            }
        )
        self.assertEqual(bank_account.l10n_py_document_type, "ci")
        self.assertEqual(bank_account.l10n_py_document_number, "1234567")

    def test_document_type_without_number_fails(self):
        """Tipo de documento sin número debe levantar ValidationError."""
        with self.assertRaises(ValidationError):
            self.PartnerBank.create(
                {
                    "acc_number": "SIPAP-DOC-BAD-1",
                    "partner_id": self.partner.id,
                    "l10n_py_document_type": "ruc",
                }
            )

    def test_document_number_without_type_fails(self):
        """Número de documento sin tipo debe levantar ValidationError."""
        with self.assertRaises(ValidationError):
            self.PartnerBank.create(
                {
                    "acc_number": "SIPAP-DOC-BAD-2",
                    "partner_id": self.partner.id,
                    "l10n_py_document_number": "1234567",
                }
            )

    def test_cas_alias_type_and_value_together_ok(self):
        """Tipo y valor de alias CAS completos juntos: no debe fallar."""
        bank_account = self.PartnerBank.create(
            {
                "acc_number": "SIPAP-ALIAS-OK",
                "partner_id": self.partner.id,
                "l10n_py_cas_alias_type": "phone",
                "l10n_py_cas_alias_value": "0981123456",
            }
        )
        self.assertEqual(bank_account.l10n_py_cas_alias_type, "phone")
        self.assertEqual(bank_account.l10n_py_cas_alias_value, "0981123456")

    def test_cas_alias_type_without_value_fails(self):
        """Tipo de alias CAS sin valor debe levantar ValidationError."""
        with self.assertRaises(ValidationError):
            self.PartnerBank.create(
                {
                    "acc_number": "SIPAP-ALIAS-BAD-1",
                    "partner_id": self.partner.id,
                    "l10n_py_cas_alias_type": "email",
                }
            )

    def test_cas_alias_value_without_type_fails(self):
        """Valor de alias CAS sin tipo debe levantar ValidationError."""
        with self.assertRaises(ValidationError):
            self.PartnerBank.create(
                {
                    "acc_number": "SIPAP-ALIAS-BAD-2",
                    "partner_id": self.partner.id,
                    "l10n_py_cas_alias_value": "someone@example.com",
                }
            )
