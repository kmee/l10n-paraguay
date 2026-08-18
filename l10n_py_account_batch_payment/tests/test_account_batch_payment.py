from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "l10n_py")
class TestAccountBatchPayment(TransactionCase):
    """Tests del framework plugable de exportación de lote SIPAP.

    Estos tests NO dependen de ningún módulo exportador real (como el
    futuro módulo ISO 20022) ni de la red/Bancard. Registran un
    exportador "fake" en tiempo de ejecución, vía mock/monkeypatch
    (documentado explícitamente como tal en cada test), únicamente para
    validar el mecanismo de dispatch (selection extensible + método
    `_l10n_py_export_<codigo>`) implementado en `account_batch_payment.py`.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.BatchPayment = cls.env["account.batch.payment"]
        cls.company = cls.env.ref("base.main_company")
        cls.bank = cls.env["res.bank"].create({"name": "Banco SIPAP Test"})
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "SIPAP-JOURNAL-BANK",
                "partner_id": cls.company.partner_id.id,
                "bank_id": cls.bank.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "SIPAP Test Bank",
                "type": "bank",
                "code": "SIPBT",
                "company_id": cls.company.id,
                "bank_account_id": cls.partner_bank.id,
            }
        )

    def _new_batch(self):
        # Usamos un registro virtual (`.new`) en lugar de crear un
        # account.batch.payment real, ya que este último exige pagos
        # (`payment_ids`) ya conciliables/posteados para poder crearse.
        # El dispatch que queremos probar no depende de eso.
        return self.BatchPayment.new(
            {
                "journal_id": self.journal.id,
                "batch_type": "outbound",
            }
        )

    def test_get_batch_export_bank(self):
        """El banco de referencia es el del bank_account_id del diario."""
        batch = self._new_batch()
        self.assertEqual(batch._l10n_py_get_batch_export_bank(), self.bank)

    def test_no_exporter_registered_raises_user_error(self):
        """Sin código de exportación configurado, debe fallar con UserError."""
        self.bank.write({"l10n_py_batch_export_code": False})
        batch = self._new_batch()
        with self.assertRaises(UserError):
            batch._l10n_py_generate_batch_file()

    def test_export_code_without_method_raises_user_error(self):
        """Código configurado pero sin método implementado: UserError."""
        selection_field = self.env["res.bank"]._fields["l10n_py_batch_export_code"]
        # Monkeypatch: agregamos temporalmente un valor al selection para
        # simular que un módulo exportador registró su código, sin que
        # exista el método `_l10n_py_export_<codigo>` correspondiente
        # (simula un módulo mal instalado/incompleto).
        with mock.patch.object(
            selection_field,
            "selection",
            selection_field.selection + [("fake_missing", "Fake Missing")],
        ):
            self.bank.write({"l10n_py_batch_export_code": "fake_missing"})
            batch = self._new_batch()
            with self.assertRaises(UserError):
                batch._l10n_py_generate_batch_file()

    def test_dispatch_to_registered_fake_exporter(self):
        """Con un exportador fake registrado, el dispatch debe invocarlo."""
        selection_field = self.env["res.bank"]._fields["l10n_py_batch_export_code"]
        fake_result = {"file": b"ZmFrZQ==", "filename": "fake_sipap_batch.txt"}

        def _fake_exporter(batch_self):
            return fake_result

        # Monkeypatch doble: (1) extendemos el selection del banco con un
        # código fake, simulando que un módulo exportador se instaló, y
        # (2) inyectamos el método `_l10n_py_export_fake_bank` en la clase
        # de account.batch.payment, simulando la implementación que ese
        # módulo exportador (ej. ISO 20022) proveería.
        with (
            mock.patch.object(
                selection_field,
                "selection",
                selection_field.selection + [("fake_bank", "Fake Bank Exporter")],
            ),
            mock.patch.object(
                type(self.BatchPayment),
                "_l10n_py_export_fake_bank",
                _fake_exporter,
                create=True,
            ),
        ):
            self.bank.write({"l10n_py_batch_export_code": "fake_bank"})
            batch = self._new_batch()
            result = batch._l10n_py_generate_batch_file()

        self.assertEqual(result, fake_result)
