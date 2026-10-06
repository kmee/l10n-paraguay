from odoo.tests import tagged

from .test_libro_common import LibroCommonCase


@tagged("post_install", "-at_install", "l10n_py", "l10n_py_libros")
class TestLibroMaquila(LibroCommonCase):
    """Documents of a maquiladora in the Registro de Comprobantes (DNIT
    technical specification, 06/2021): export invoice with IVA Exonerado
    (Art. 100 Ley 6380/2019), domestic purchases, autofactura and foreign
    supplier invoices."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_br = cls.env.ref("base.br")
        cls.matriz = cls.env["res.partner"].create(
            {
                "name": "Matriz Brasil Ltda",
                "country_id": cls.country_br.id,
                "vat": "11222333000181",
                "l10n_latam_identification_type_id": cls.env.ref(
                    "l10n_latam_base.it_vat"
                ).id,
            }
        )
        cls.foreign_supplier = cls.env["res.partner"].create(
            {
                "name": "Steel Supplier Co",
                "country_id": cls.env.ref("base.cn").id,
                "l10n_latam_identification_type_id": cls.env.ref(
                    "l10n_latam_base.it_vat"
                ).id,
            }
        )
        cls.tax_exonerado = cls.env["account.tax"].create(
            {
                "name": "Exonerado Libros Test",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "l10n_py_iva_affectation": "2",
            }
        )

    def test_export_invoice_exonerado_in_ventas(self):
        invoice = self._create_invoice(
            "out_invoice",
            [(self.product, self.tax_exonerado, 5000000.0)],
            partner_id=self.matriz.id,
        )
        invoice.action_post()
        self.assertEqual(invoice.l10n_py_amount_exonerado, 5000000.0)
        self.assertEqual(invoice.l10n_py_amount_exempt, 0.0)
        libro = self._create_libro("ventas")
        libro.action_generate_lines()
        line = libro.line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.state, "ok", line.error_message)
        # Field 11 "monto no gravado o exento" carries the exonerated amount.
        self.assertEqual(line.f_monto_exento, 5000000)
        self.assertEqual(line.f_monto_gravado_10, 0)
        self.assertEqual(line.f_monto_gravado_5, 0)
        self.assertEqual(line.f_monto_total, 5000000)
        # Table 3: foreign buyer with tax id -> 17, never RUC (11).
        self.assertEqual(line.f_tipo_identificacion, "17")
        self.assertEqual(line.f_numero_identificacion, "11222333000181")
        self.assertEqual(line.f_nombre_razon_social, "Matriz Brasil Ltda")
        self.assertEqual(line.f_tipo_comprobante, "109")

    def test_exempt_and_exonerado_on_same_invoice(self):
        invoice = self._create_invoice(
            "out_invoice",
            [
                (self.product, self.tax_exonerado, 3000.0),
                (self.product, self.tax_exempt, 1000.0),
                (self.product, self.tax_10, 1100.0),
            ],
            partner_id=self.matriz.id,
        )
        invoice.action_post()
        libro = self._create_libro("ventas")
        libro.action_generate_lines()
        line = libro.line_ids
        self.assertEqual(line.state, "ok", line.error_message)
        self.assertEqual(line.f_monto_exento, 4000)
        self.assertEqual(line.f_monto_gravado_10, 1100)
        self.assertEqual(line.f_monto_total, 5100)

    def test_foreign_passport_maps_to_13(self):
        tourist = self.env["res.partner"].create(
            {
                "name": "Foreign Buyer",
                "country_id": self.country_br.id,
                "vat": "FX123456",
                "l10n_latam_identification_type_id": self.env.ref(
                    "l10n_latam_base.it_pass"
                ).id,
            }
        )
        invoice = self._create_invoice(
            "out_invoice",
            [(self.product, self.tax_10, 1100.0)],
            partner_id=tourist.id,
        )
        invoice.action_post()
        libro = self._create_libro("ventas")
        libro.action_generate_lines()
        self.assertEqual(libro.line_ids.f_tipo_identificacion, "13")

    def test_domestic_purchase_enters_compras(self):
        bill = self._create_invoice(
            "in_invoice",
            [(self.product, self.tax_10_purchase, 1100.0)],
            l10n_py_libro_supplier_timbrado="87654323",
            l10n_py_libro_supplier_number="001-001-0000003",
        )
        bill.action_post()
        libro = self._create_libro("compras")
        libro.action_generate_lines()
        line = libro.line_ids
        self.assertEqual(line.move_id, bill)
        self.assertEqual(line.state, "ok", line.error_message)
        self.assertEqual(line.f_tipo_identificacion, "11")
        self.assertEqual(line.f_monto_gravado_10, 1100)

    def test_autofactura_from_non_taxpayer(self):
        person = self.env["res.partner"].create(
            {
                "name": "Recolector de chatarra",
                "country_id": self.country_py.id,
                "vat": "1234567",
                "l10n_latam_identification_type_id": self.env.ref(
                    "l10n_py_base.it_ci"
                ).id,
                "l10n_py_taxpayer_type": "2",
            }
        )
        bill = self._create_invoice(
            "in_invoice",
            [(self.product, self.tax_exempt_purchase, 250000.0)],
            doc_type=self.doc_type_autofactura,
            partner_id=person.id,
            l10n_py_libro_supplier_timbrado="87654324",
            l10n_py_libro_supplier_number="001-001-0000004",
        )
        bill.action_post()
        libro = self._create_libro("compras")
        libro.action_generate_lines()
        line = libro.line_ids
        self.assertEqual(line.state, "ok", line.error_message)
        self.assertEqual(line.f_tipo_comprobante, "101")
        self.assertEqual(line.f_tipo_identificacion, "12")
        # 101: amounts by rate are zero, only the total (spec, Compras).
        self.assertEqual(line.f_monto_exento, 0)
        self.assertEqual(line.f_monto_total, 250000)

    def test_foreign_supplier_invoice_not_in_compras(self):
        bill = self._create_invoice(
            "in_invoice",
            [(self.product, False, 9000.0)],
            partner_id=self.foreign_supplier.id,
        )
        bill.action_post()
        domestic = self._create_invoice(
            "in_invoice",
            [(self.product, self.tax_10_purchase, 1100.0)],
            l10n_py_libro_supplier_timbrado="87654325",
            l10n_py_libro_supplier_number="001-001-0000005",
        )
        domestic.action_post()
        libro = self._create_libro("compras")
        libro.action_generate_lines()
        self.assertEqual(libro.line_ids.move_id, domestic)
        note = libro.message_ids.filtered(lambda m: bill.name in (m.body or ""))
        self.assertTrue(note)
        libro.action_confirm()
        self.assertEqual(libro.state, "confirmed")
