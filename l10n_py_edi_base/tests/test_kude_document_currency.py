# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import re

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_py_edi_base.services.kude_pdf import (
    KudeFeDocumentCurrency,
    build_kude,
    format_amount,
)

_ITEM = """
      <gCamItem>
        <dCodInt>{code}</dCodInt>
        <dDesProSer>{name}</dDesProSer>
        <cUniMed>77</cUniMed>
        <dDesUniMed>UNI</dDesUniMed>
        <dCantProSer>{qty}</dCantProSer>
        <gValorItem>
          <dPUniProSer>{price}</dPUniProSer>
          <dTotBruOpeItem>{total}</dTotBruOpeItem>
          <gValorRestaItem>
            <dDescItem>0</dDescItem>
            <dTotOpeItem>{total}</dTotOpeItem>
          </gValorRestaItem>
        </gValorItem>
        <gCamIVA>
          <iAfecIVA>2</iAfecIVA>
          <dDesAfecIVA>Exonerado</dDesAfecIVA>
          <dTasaIVA>0</dTasaIVA>
        </gCamIVA>
      </gCamItem>"""

_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rDE xmlns="http://ekuatia.set.gov.py/sifen/xsd">
  <dVerFor>150</dVerFor>
  <DE Id="01801500117001001000000122026100612035153276">
    <gTimb>
      <iTiDE>1</iTiDE>
      <dDesTiDE>Factura electrónica</dDesTiDE>
      <dNumTim>11126010</dNumTim>
      <dEst>001</dEst>
      <dPunExp>001</dPunExp>
      <dNumDoc>0000001</dNumDoc>
    </gTimb>
    <gDatGralOpe>
      <dFeEmiDE>2026-10-06T10:00:00</dFeEmiDE>
      <gOpeCom>
        <cMoneOpe>{currency}</cMoneOpe>
        <dDesMoneOpe>{currency_name}</dDesMoneOpe>
        {rate}
      </gOpeCom>
    </gDatGralOpe>
    <gDtipDE>
      <gCamCond>
        <iCondOpe>1</iCondOpe>
        <dDCondOpe>Contado</dDCondOpe>
        <gPaConEIni>
          <iTiPago>1</iTiPago>
          <dDesTiPag>Efectivo</dDesTiPag>
          <dMonTiPag>{total}</dMonTiPag>
          <cMoneTiPag>{currency}</cMoneTiPag>
        </gPaConEIni>
      </gCamCond>{items}
    </gDtipDE>
    <gTotSub>
      <dSubExe>0</dSubExe>
      <dSubExo>{total}</dSubExo>
      <dSub5>0</dSub5>
      <dSub10>0</dSub10>
      <dTotOpe>{total}</dTotOpe>
      <dTotGralOpe>{total}</dTotGralOpe>
      <dIVA5>0</dIVA5>
      <dIVA10>0</dIVA10>
      <dTotIVA>0</dTotIVA>
      {total_gs}
    </gTotSub>
  </DE>
</rDE>
"""


def _xml_usd():
    items = _ITEM.format(
        code="IC-ACERO", name="Perfil de acero", qty=1200, price=2.1, total="2520.00"
    ) + _ITEM.format(
        code="IC-ALUM", name="Perfil de aluminio", qty=800, price=5.8, total="4640.00"
    )
    return _XML.format(
        currency="USD",
        currency_name="Dólar americano",
        rate="<dCondTiCam>1</dCondTiCam><dTiCam>7350</dTiCam>",
        total="7160.00",
        total_gs="<dTotalGs>52626000</dTotalGs>",
        items=items,
    )


@tagged("post_install", "-at_install", "l10n_py")
class TestKudeDocumentCurrency(TransactionCase):
    """KuDE amounts in the currency of the document, with the Exonerado
    subtotal (pykude 0.1.0 prints every amount as guaraníes)."""

    def _pdf_text(self, kude):
        kude.set_compression(False)
        return bytes(kude.output()).decode("latin-1")

    def test_format_amount(self):
        self.assertEqual(format_amount("1500000.4", "PYG"), "Gs. 1.500.000")
        self.assertEqual(format_amount("2520", "USD"), "USD 2.520,00")
        self.assertEqual(format_amount("2.1", "USD", max_decimals=4), "USD 2,10")
        self.assertEqual(format_amount("2.1234", "USD", max_decimals=4), "USD 2,1234")

    def test_invoice_in_usd(self):
        kude = build_kude(_xml_usd())
        self.assertIsInstance(kude, KudeFeDocumentCurrency)
        self.assertEqual(
            [item["total_item"] for item in kude.data["items"]],
            ["2520.00", "4640.00"],
        )
        text = self._pdf_text(kude)
        for expected in (
            "USD 2,10",
            "USD 2.520,00",
            "USD 4.640,00",
            "Exonerado",
            "Subtotal Exonerado: USD 7.160,00",
            "TOTAL GENERAL: USD 7.160,00",
            "Gs. 7.350",
            "Gs. 52.626.000",
        ):
            self.assertIn(expected, text)
        # guaraníes only for the exchange rate and the total in guaraníes
        self.assertEqual(
            re.findall(r"Gs\. [\d.]+", text), ["Gs. 7.350", "Gs. 52.626.000"]
        )

    def test_invoice_in_pyg(self):
        items = _ITEM.format(
            code="P1", name="Servicio", qty=2, price=55000, total="110000"
        )
        xml = _XML.format(
            currency="PYG",
            currency_name="Guarani",
            rate="",
            total="110000",
            total_gs="",
            items=items,
        )
        text = self._pdf_text(build_kude(xml))
        self.assertIn("Gs. 110.000", text)
        self.assertIn("Subtotal Exonerado: Gs. 110.000", text)
        self.assertNotIn("Total en Guaran", text)
