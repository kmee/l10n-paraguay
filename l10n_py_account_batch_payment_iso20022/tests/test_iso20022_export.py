# l10n_py_account_batch_payment_iso20022/tests/test_iso20022_export.py

import base64

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

PAIN_001_NS = {"p": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"}


@tagged("post_install", "-at_install", "l10n_py")
class TestIso20022Export(TransactionCase):
    """Tests del exportador ISO 20022 genérico (pain.001.001.09).

    Cubre: (1) el contrato de retorno `{'file': <base64>, 'filename': ...}`,
    (2) la estructura mínima del XML generado vía aserciones lxml, y (3) la
    lectura del umbral SPI/LBTR desde `res.company` en lugar de un valor
    fijo en el código.

    Limitación conocida y documentada a propósito (ver también el README):
    no fue posible, en este entorno de pruebas (sandbox de ejecución sin
    acceso a internet), descargar los XSD oficiales de
    https://www.iso20022.org para validar el XML generado contra el schema
    formal. La validación aquí se limita a aserciones de estructura
    (presencia/orden de elementos, atributos, y coherencia de
    NbOfTxs/CtrlSum) hechas directamente con `lxml.etree`. Esto NO
    reemplaza una validación XSD real, que debe hacerse antes de usar este
    exportador en producción.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.BatchPayment = cls.env["account.batch.payment"]
        cls.Payment = cls.env["account.payment"]
        cls.company = cls.env.ref("base.main_company")

        # Banco/canal por el cual se envía el lote (banco del diario).
        cls.sipap_bank = cls.env["res.bank"].create(
            {
                "name": "Banco SIPAP ISO20022 Test",
                "l10n_py_sipap_code": "0001",
                "l10n_py_batch_export_code": "iso20022",
            }
        )
        cls.journal_partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "JOURNAL-ACC-0001",
                "partner_id": cls.company.partner_id.id,
                "bank_id": cls.sipap_bank.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "SIPAP ISO20022 Test Bank",
                "type": "bank",
                "code": "SPISO",
                "company_id": cls.company.id,
                "bank_account_id": cls.journal_partner_bank.id,
                "currency_id": cls.company.currency_id.id,
            }
        )

        # Beneficiarios.
        cls.beneficiary_bank = cls.env["res.bank"].create(
            {"name": "Banco Beneficiario Test", "l10n_py_sipap_code": "0002"}
        )
        cls.partner_1 = cls.env["res.partner"].create({"name": "Proveedor Uno"})
        cls.partner_bank_1 = cls.env["res.partner.bank"].create(
            {
                "acc_number": "BENEF-ACC-0001",
                "partner_id": cls.partner_1.id,
                "bank_id": cls.beneficiary_bank.id,
            }
        )
        cls.partner_2 = cls.env["res.partner"].create({"name": "Proveedor Dos"})
        cls.partner_bank_2 = cls.env["res.partner.bank"].create(
            {
                "acc_number": "BENEF-ACC-0002",
                "partner_id": cls.partner_2.id,
                "bank_id": cls.beneficiary_bank.id,
            }
        )

        cls.payment_1 = cls.Payment.create(
            {
                "payment_type": "outbound",
                "partner_type": "supplier",
                "partner_id": cls.partner_1.id,
                "partner_bank_id": cls.partner_bank_1.id,
                "amount": 1_000_000,
                "currency_id": cls.company.currency_id.id,
                "journal_id": cls.journal.id,
                "memo": "Pago de prueba uno",
            }
        )
        cls.payment_2 = cls.Payment.create(
            {
                "payment_type": "outbound",
                "partner_type": "supplier",
                "partner_id": cls.partner_2.id,
                "partner_bank_id": cls.partner_bank_2.id,
                "amount": 2_500_000,
                "currency_id": cls.company.currency_id.id,
                "journal_id": cls.journal.id,
                "memo": "Pago de prueba dos",
            }
        )

    def _new_batch(self, payments):
        # Registro virtual: igual estrategia que
        # `l10n_py_account_batch_payment/tests/test_account_batch_payment.py`,
        # ya que `account.batch.payment` (Enterprise) exige que los pagos
        # ya estén en un estado conciliable/posteado para poder agregarse
        # a un lote persistido. El export en sí no depende de ese estado.
        return self.BatchPayment.new(
            {
                "journal_id": self.journal.id,
                "batch_type": "outbound",
                "payment_ids": [(6, 0, payments.ids)],
            }
        )

    def _export(self, payments):
        batch = self._new_batch(payments)
        return batch, batch._l10n_py_export_iso20022()

    def test_export_return_contract(self):
        """Retorna dict con 'file' (base64 válido) y 'filename'."""
        payments = self.payment_1 + self.payment_2
        _batch, result = self._export(payments)
        self.assertIn("file", result)
        self.assertIn("filename", result)
        self.assertTrue(result["filename"].endswith(".xml"))
        # No debe lanzar excepción: confirma que 'file' es base64 válido.
        decoded = base64.b64decode(result["file"], validate=True)
        self.assertTrue(decoded.startswith(b"<?xml"))

    def test_export_dispatched_via_generic_framework(self):
        """El framework del módulo 1 despacha correctamente a este exportador.

        Usa el mismo mecanismo genérico `_l10n_py_generate_batch_file()`
        (no solo la llamada directa a `_l10n_py_export_iso20022()`), para
        confirmar que el `selection_add` + el método `_l10n_py_export_
        iso20022` quedaron correctamente registrados como exportador del
        banco.
        """
        payments = self.payment_1 + self.payment_2
        batch = self._new_batch(payments)
        result = batch._l10n_py_generate_batch_file()
        self.assertIn("file", result)
        self.assertIn("filename", result)

    def test_xml_structure(self):
        """Estructura mínima esperada del pain.001.001.09 (vía lxml)."""
        payments = self.payment_1 + self.payment_2
        _batch, result = self._export(payments)
        xml_bytes = base64.b64decode(result["file"])
        root = etree.fromstring(xml_bytes)

        self.assertEqual(
            root.tag, "{urn:iso:std:iso:20022:tech:xsd:pain.001.001.09}Document"
        )

        grp_hdr = root.find(".//p:GrpHdr", namespaces=PAIN_001_NS)
        self.assertIsNotNone(grp_hdr)
        self.assertIsNotNone(grp_hdr.find("p:MsgId", namespaces=PAIN_001_NS))
        self.assertIsNotNone(grp_hdr.find("p:CreDtTm", namespaces=PAIN_001_NS))

        nb_of_txs = grp_hdr.find("p:NbOfTxs", namespaces=PAIN_001_NS)
        ctrl_sum = grp_hdr.find("p:CtrlSum", namespaces=PAIN_001_NS)
        self.assertEqual(nb_of_txs.text, str(len(payments)))
        self.assertEqual(float(ctrl_sum.text), sum(payments.mapped("amount")))

        pmt_infs = root.findall(".//p:PmtInf", namespaces=PAIN_001_NS)
        self.assertEqual(len(pmt_infs), 1)
        pmt_inf = pmt_infs[0]
        self.assertEqual(pmt_inf.find("p:PmtMtd", namespaces=PAIN_001_NS).text, "TRF")

        cdt_trf_tx_infs = root.findall(".//p:CdtTrfTxInf", namespaces=PAIN_001_NS)
        self.assertEqual(len(cdt_trf_tx_infs), len(payments))

        # Cada CdtTrfTxInf debe traer beneficiario, cuenta y monto.
        for tx_inf, payment in zip(cdt_trf_tx_infs, payments, strict=False):
            cdtr_nm = tx_inf.find(".//p:Cdtr/p:Nm", namespaces=PAIN_001_NS)
            self.assertEqual(cdtr_nm.text, payment.partner_id.name)
            instd_amt = tx_inf.find(".//p:InstdAmt", namespaces=PAIN_001_NS)
            self.assertEqual(float(instd_amt.text), payment.amount)

    def test_xsd_validation_not_available_in_sandbox(self):
        """Documenta la limitación: no hay acceso a internet en el sandbox.

        Se intentó, durante el desarrollo de este exportador, descargar los
        XSD oficiales del pain.001.001.09 desde https://www.iso20022.org
        para validar el XML generado contra el schema formal. El entorno
        de ejecución de este test no tiene acceso a internet, por lo que
        esa descarga no es posible aquí. No se generó ni vendorizó ningún
        XSD "fake" como sustituto: hacerlo daría una falsa sensación de
        validación formal. Ver también README (sección de limitaciones).
        """
        self.skipTest(
            "Validación contra el XSD oficial pain.001.001.09 requiere "
            "descargarlo de https://www.iso20022.org; sin acceso a "
            "internet en este entorno de pruebas. La estructura del XML "
            "generado sí se valida (ver test_xml_structure), pero eso no "
            "reemplaza la validación XSD formal antes de producción."
        )

    def test_spi_lbtr_category_follows_company_threshold(self):
        """La categoría SPI/LBTR cambia según el umbral configurado.

        No se compara contra ningún valor "oficial" del BCP (no hay
        confirmación de cuál es); solo se confirma que el mecanismo de
        configuración (campo en `res.company`) efectivamente controla el
        resultado, que es lo que se puede probar sin esa confirmación.
        """
        batch = self._new_batch(self.payment_1)

        self.company.l10n_py_iso20022_spi_lbtr_threshold = 10_000_000
        category_below = batch._l10n_py_iso20022_category_purpose(
            self.payment_1.amount, self.company.currency_id
        )
        self.assertEqual(category_below, "SPI")

        self.company.l10n_py_iso20022_spi_lbtr_threshold = 500_000
        category_above = batch._l10n_py_iso20022_category_purpose(
            self.payment_1.amount, self.company.currency_id
        )
        self.assertEqual(category_above, "LBTR")

    def test_spi_lbtr_category_reflected_in_xml(self):
        """El CtgyPurp/Prtry del XML refleja el umbral configurado."""
        self.company.l10n_py_iso20022_spi_lbtr_threshold = 500_000
        _batch, result = self._export(self.payment_1)
        xml_bytes = base64.b64decode(result["file"])
        root = etree.fromstring(xml_bytes)
        prtry = root.find(".//p:CtgyPurp/p:Prtry", namespaces=PAIN_001_NS)
        self.assertEqual(prtry.text, "LBTR")

    def test_foreign_currency_payment_is_always_lbtr(self):
        """Un pago en moneda distinta a la de la empresa es siempre LBTR.

        Refleja la definición funcional de LBTR (alto valor **o** moneda
        extranjera), independientemente del umbral configurado.
        """
        self.company.l10n_py_iso20022_spi_lbtr_threshold = 999_999_999
        foreign_currency = self.env.ref("base.USD")
        if foreign_currency == self.company.currency_id:
            foreign_currency = self.env.ref("base.EUR")
        batch = self._new_batch(self.payment_1)
        category = batch._l10n_py_iso20022_category_purpose(
            self.payment_1.amount, foreign_currency
        )
        self.assertEqual(category, "LBTR")
