# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""KuDE PDF in the currency of the document.

pykude 0.1.0 formats every amount as guaraníes (integer, "Gs."), reads the item
total from a path where SIFEN does not put it (dTotOpeItem lives in
gValorRestaItem) and has no line for the IVA Exonerado subtotal (dSubExo).
Invoices, credit notes and debit notes are drawn here with the operation
currency (cMoneOpe), the exchange rate (dTiCam) and the total in guaraníes
(dTotalGs); the other document types still go to pykude.auto_kude.
"""

from pykude.base import FOOTER_HEIGHT
from pykude.common_sections import draw_doc_asociado, draw_motivo_emision
from pykude.kude_fe.kude_fe import KudeFe
from pykude.kude_fe.sections import (
    draw_header,
    draw_receptor,
    draw_test_watermark,
)
from pykude.kude_nce.kude_nce import KudeNce
from pykude.kude_nde.kude_nde import KudeNde
from pykude.utils import format_fecha, format_number
from pykude.xml_helpers import NS, get_text, parse_xml

PYG = "PYG"


def _to_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def format_amount(value, currency=PYG, max_decimals=2):
    """Guaraníes without decimals ("Gs. 1.500.000"); other currencies with
    the ISO code and at least two decimals ("USD 2.520,00")."""
    number = _to_float(value)
    if not currency or currency == PYG:
        return f"Gs. {format_number(round(number))}"
    text = f"{number:,.{max_decimals}f}"
    if max_decimals > 2:
        integer, decimals = text.split(".")
        text = f"{integer}.{decimals.rstrip('0').ljust(2, '0')}"
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{currency} {text}"


class _DocumentCurrencyMixin:
    """Draw items, operation and totals in the currency of the document."""

    def __init__(self, xml, config=None):
        root = parse_xml(xml)
        self._l10n_py_de = root.find(".//sifen:DE", NS)
        if self._l10n_py_de is None:
            self._l10n_py_de = root
        super().__init__(xml=xml, config=config)

    def _l10n_py_complete_data(self):
        de = self._l10n_py_de
        data = self.data
        data["moneda"] = data.get("moneda") or PYG
        data["tipo_cambio"] = get_text(
            de, "sifen:gDatGralOpe/sifen:gOpeCom/sifen:dTiCam"
        )
        item_nodes = de.findall("sifen:gDtipDE/sifen:gCamItem", NS)
        for item, node in zip(data.get("items", []), item_nodes, strict=False):
            rest = "sifen:gValorItem/sifen:gValorRestaItem"
            if not item.get("total_item"):
                item["total_item"] = get_text(node, f"{rest}/sifen:dTotOpeItem", "0")
            if not item.get("descuento"):
                item["descuento"] = get_text(node, f"{rest}/sifen:dDescItem", "0")

    def _amount(self, value, max_decimals=2):
        return format_amount(value, self.data.get("moneda"), max_decimals)

    def _draw_operacion(self):
        pdf, data, config = self, self.data, self.config
        pdf.set_x(config.margins.left)
        y_start = pdf.get_y()
        page_width = pdf.w - config.margins.left - config.margins.right
        col_w = page_width / 3
        condicion = data.get("condicion", {})

        pdf.set_font(config.font_type.value, "B", 7)
        pdf.cell(
            page_width,
            4,
            "DATOS DE LA OPERACIÓN",
            align="C",
            new_x="LEFT",
            new_y="NEXT",
        )
        pdf.set_font(config.font_type.value, "", 7)
        pdf.set_x(config.margins.left)
        pdf.cell(col_w, 4, f"Condición: {condicion.get('descripcion', '')}")
        moneda = data.get("desc_moneda") or data.get("moneda")
        pdf.cell(col_w, 4, f"Moneda: {moneda}")
        pdf.cell(
            col_w,
            4,
            f"Tipo Trans.: {data.get('desc_tipo_transaccion', '')}",
            new_x="LEFT",
            new_y="NEXT",
        )
        if data.get("moneda") != PYG and data.get("tipo_cambio"):
            pdf.set_x(config.margins.left)
            pdf.cell(
                page_width,
                4,
                f"Tipo de cambio: {format_amount(data['tipo_cambio'], 'PYG')}",
                new_x="LEFT",
                new_y="NEXT",
            )
        if condicion.get("pagos"):
            pagos = [
                f"{pago.get('descripcion', '')} - "
                f"{format_amount(pago.get('monto'), pago.get('moneda') or PYG)}"
                for pago in condicion["pagos"]
            ]
            pdf.set_x(config.margins.left)
            pdf.cell(
                page_width,
                4,
                f"Forma de Pago: {'; '.join(pagos)}",
                new_x="LEFT",
                new_y="NEXT",
            )
        pdf.set_x(config.margins.left)
        fecha = format_fecha(data.get("fecha_emision", ""))
        pdf.cell(
            page_width, 4, f"Fecha de Emisión: {fecha}", new_x="LEFT", new_y="NEXT"
        )
        pdf.rect(config.margins.left, y_start, page_width, pdf.get_y() - y_start)

    def _draw_items_header(self, cols):
        self.set_font(self.config.font_type.value, "B", 7)
        self.set_x(self.config.margins.left)
        for label, width in cols:
            self.cell(width, 5, label, border=1, align="C")
        self.ln()

    def _draw_items(self):
        pdf, config = self, self.config
        page_width = pdf.w - config.margins.left - config.margins.right
        pdf.set_x(config.margins.left)
        pdf.set_font(config.font_type.value, "B", 7)
        pdf.cell(
            page_width, 4, "DETALLE DE ITEMS", align="C", new_x="LEFT", new_y="NEXT"
        )
        cols = [
            ("Cód.", 18),
            ("Descripción", page_width - 18 - 15 - 18 - 28 - 22 - 28),
            ("Unid.", 15),
            ("Cant.", 18),
            ("P. Unit.", 28),
            ("IVA", 22),
            ("Subtotal", 28),
        ]
        self._draw_items_header(cols)
        pdf.set_font(config.font_type.value, "", 7)
        items = self.data.get("items", [])
        for item in items:
            if pdf.get_y() + 5 > pdf.h - config.margins.bottom - FOOTER_HEIGHT - 30:
                pdf.add_page()
                self._draw_items_header(cols)
                pdf.set_font(config.font_type.value, "", 7)
            pdf.set_x(config.margins.left)
            pdf.cell(cols[0][1], 5, item.get("codigo", "")[:8], border=1)
            pdf.cell(cols[1][1], 5, item.get("descripcion", "")[:50], border=1)
            pdf.cell(cols[2][1], 5, item.get("desc_unidad", ""), border=1, align="C")
            pdf.cell(
                cols[3][1],
                5,
                format_number(item.get("cantidad", "0")),
                border=1,
                align="R",
            )
            pdf.cell(
                cols[4][1],
                5,
                self._amount(item.get("precio_unitario"), max_decimals=4),
                border=1,
                align="R",
            )
            # iAfecIVA 2 = Exonerado, 3 = Exento: the rate alone reads "0%"
            afec = {"2": "Exonerado", "3": "Exento"}.get(item.get("afec_iva"))
            pdf.cell(
                cols[5][1],
                5,
                afec or f"{item.get('tasa_iva', '0')}%",
                border=1,
                align="C",
            )
            pdf.cell(
                cols[6][1],
                5,
                self._amount(item.get("total_item")),
                border=1,
                align="R",
            )
            pdf.ln()
        if not items:
            pdf.set_x(config.margins.left)
            pdf.cell(page_width, 5, "Sin items", border=1, align="C")
            pdf.ln()

    def _draw_totales(self):
        pdf, config = self, self.config
        if pdf.get_y() + 30 > pdf.h - config.margins.bottom - FOOTER_HEIGHT:
            pdf.add_page()
        pdf.set_x(config.margins.left)
        y_start = pdf.get_y()
        page_width = pdf.w - config.margins.left - config.margins.right
        col_w = page_width / 4
        totales = self.data.get("totales", {})
        amount = self._amount

        pdf.set_font(config.font_type.value, "B", 7)
        pdf.cell(
            page_width,
            4,
            "SUBTOTALES / TOTALES",
            align="C",
            new_x="LEFT",
            new_y="NEXT",
        )
        pdf.set_font(config.font_type.value, "", 7)
        rows = [
            [
                f"Subtotal Exento: {amount(totales.get('sub_exento'))}",
                f"Subtotal Exonerado: {amount(totales.get('sub_exonerado'))}",
                f"Subtotal IVA 5%: {amount(totales.get('sub_5'))}",
                f"Subtotal IVA 10%: {amount(totales.get('sub_10'))}",
            ],
            [
                f"Liq. IVA 5%: {amount(totales.get('iva_5'))}",
                f"Liq. IVA 10%: {amount(totales.get('iva_10'))}",
                f"Total IVA: {amount(totales.get('total_iva'))}",
                "",
            ],
        ]
        for row in rows:
            pdf.set_x(config.margins.left)
            for text in row[:-1]:
                pdf.cell(col_w, 4, text)
            pdf.cell(col_w, 4, row[-1], new_x="LEFT", new_y="NEXT")
        if _to_float(totales.get("total_descuento")) > 0:
            pdf.set_x(config.margins.left)
            pdf.cell(
                page_width,
                4,
                f"Total Descuento: {amount(totales.get('total_descuento'))}",
                new_x="LEFT",
                new_y="NEXT",
            )
        pdf.set_x(config.margins.left)
        pdf.set_font(config.font_type.value, "B", 9)
        pdf.cell(
            page_width,
            6,
            f"TOTAL GENERAL: {amount(totales.get('total_general'))}",
            align="R",
            new_x="LEFT",
            new_y="NEXT",
        )
        if self.data.get("moneda") != PYG and _to_float(totales.get("total_gs")):
            pdf.set_x(config.margins.left)
            pdf.set_font(config.font_type.value, "", 7)
            pdf.cell(
                page_width,
                4,
                f"Total en Guaraníes: {format_amount(totales['total_gs'], PYG)}",
                align="R",
                new_x="LEFT",
                new_y="NEXT",
            )
        pdf.rect(config.margins.left, y_start, page_width, pdf.get_y() - y_start)

    def _draw(self):
        self._l10n_py_complete_data()
        if self.config.ambiente == 2:
            draw_test_watermark(self, self.config)
        draw_header(self, self.data, self.config)
        draw_receptor(self, self.data, self.config)
        if self._l10n_py_is_note:
            draw_motivo_emision(self, self.data, self.config, self.data.get("cam_ncde"))
            draw_doc_asociado(self, self.data, self.config)
        self._draw_operacion()
        self._draw_items()
        self._draw_totales()


class KudeFeDocumentCurrency(_DocumentCurrencyMixin, KudeFe):
    _l10n_py_is_note = False


class KudeNceDocumentCurrency(_DocumentCurrencyMixin, KudeNce):
    _l10n_py_is_note = True


class KudeNdeDocumentCurrency(_DocumentCurrencyMixin, KudeNde):
    _l10n_py_is_note = True


# iTiDE: 1 factura, 5 nota de crédito, 6 nota de débito
_KUDE_CLASSES = {
    "1": KudeFeDocumentCurrency,
    "5": KudeNceDocumentCurrency,
    "6": KudeNdeDocumentCurrency,
}


def build_kude(xml, config=None):
    """KuDE object (call .output() for the PDF bytes) for a SIFEN XML"""
    root = parse_xml(xml)
    de = root.find(".//sifen:DE", NS)
    tipo = get_text(de if de is not None else root, "sifen:gTimb/sifen:iTiDE")
    kude_class = _KUDE_CLASSES.get(tipo)
    if kude_class:
        return kude_class(xml=xml, config=config)
    import pykude

    return pykude.auto_kude(xml=xml, config=config)
