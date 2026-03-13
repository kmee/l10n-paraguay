# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

"""
RDeBuilder: Converts invoice_data dict → pysifen RDe binding object.

Mapping follows SIFEN v150 Manual Técnico.
"""

import logging
from datetime import datetime

from pysifen.bindings import (
    RDe,
    TDe,
    TgCamCond,
    TgCamDEAsoc,
    TgCamFE,
    TgCamItem,
    TgCamNCDE,
    TgCamNRE,
    TgDatGralOpe,
    TgDatRec,
    TgDtipDE,
    TgEmis,
    TgOpeDE,
    TgTimb,
    TgTotSub,
)

_logger = logging.getLogger(__name__)


class RDeBuilder:
    """Build pysifen RDe object from invoice_data dict."""

    def __init__(self, invoice_data: dict, company_data: dict, cdc: str):
        self.data = invoice_data
        self.company = company_data
        self.cdc = cdc

    def build(self) -> RDe:
        """Build complete RDe."""
        tde = TDe(
            Id=self.cdc,
            gOpeDE=self._build_gOpeDE(),
            gTimb=self._build_gTimb(),
            gDatGralOpe=self._build_gDatGralOpe(),
            gDtipDE=self._build_gDtipDE(),
            gTotSub=self._build_gTotSub(),
            gCamCond=self._build_gCamCond(),
        )

        # Optional: associated documents (Grupo H)
        assoc_docs = self.data.get("documentosAsociados", [])
        if assoc_docs:
            tde.gCamDEAsoc = self._build_gCamDEAsoc(assoc_docs)

        return RDe(dVerFor="150", DE=tde)

    def _build_gOpeDE(self) -> TgOpeDE:
        """Grupo A: Operational data."""
        return TgOpeDE(
            iTipEmi=self.data.get("tipoEmision", 1),
            dCodSeg=self.data.get("codigoSeguridadAleatorio", "000000000"),
        )

    def _build_gTimb(self) -> TgTimb:
        """Grupo B: Timbrado / document identification."""
        return TgTimb(
            iTiDE=self.data.get("tipoDocumento", 1),
            dEst=self.data.get("establecimiento", "001"),
            dPunExp=self.data.get("punto", "001"),
            dNumDoc=self.data.get("numero", "0000001"),
        )

    def _build_gDatGralOpe(self) -> TgDatGralOpe:
        """Grupo C: General operation data."""
        fecha_str = self.data.get("fecha", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        return TgDatGralOpe(
            dFeEmiDE=fecha_str,
            gEmis=self._build_gEmis(),
            gDatRec=self._build_gDatRec(),
        )

    def _build_gEmis(self) -> TgEmis:
        """Grupo D: Emitter (company) data."""
        return TgEmis(
            dRucEm=self.company.get("ruc", ""),
            dDVEmi=self.company.get("dv", ""),
            dNomEmi=self.company.get("razonSocial", ""),
            dNomFanEmi=self.company.get("nombreFantasia", ""),
            dDirEmi=self.company.get("direccion", ""),
            dNumCas=self.company.get("numeroCasa", "0"),
            cDepEmi=self.company.get("departamento", 0),
            cDisEmi=self.company.get("distrito", 0),
            cCiuEmi=self.company.get("ciudad", ""),
            dTelEmi=self.company.get("telefono", ""),
            dEmailE=self.company.get("email", ""),
            dDesActEco=self.company.get("actividadEconomica", ""),
        )

    def _build_gDatRec(self) -> TgDatRec:
        """Grupo D: Receiver (customer) data."""
        cliente = self.data.get("cliente", {})
        rec = TgDatRec(
            dRucRec=cliente.get("ruc", ""),
            dNomRec=cliente.get("razonSocial", ""),
            dNomFanRec=cliente.get("nombreFantasia", ""),
            dDirRec=cliente.get("direccion", ""),
            dNumCasRec=cliente.get("numeroCasa", "0"),
        )
        if cliente.get("departamento"):
            rec.cDepRec = cliente["departamento"]
        if cliente.get("ciudad"):
            rec.cCiuRec = cliente["ciudad"]
        if cliente.get("email"):
            rec.dEmailRec = cliente["email"]
        if cliente.get("telefono"):
            rec.dTelRec = cliente["telefono"]
        if cliente.get("documentoTipo"):
            rec.iTipIDRec = cliente["documentoTipo"]
        if cliente.get("documentoNumero"):
            rec.dNumIDRec = cliente["documentoNumero"]
        return rec

    def _build_gDtipDE(self) -> TgDtipDE:
        """Grupo E: Document type specifics + items."""
        dtip = TgDtipDE()

        doc_type = self.data.get("tipoDocumento", 1)

        # Factura electrónica (tipo 1) or Autofactura (tipo 4)
        if doc_type in (1, 4):
            factura = self.data.get("factura", {})
            dtip.gCamFE = TgCamFE(
                iIndPres=factura.get("presencia", 1),
            )

        # Nota de crédito (tipo 5) or Nota de débito (tipo 6)
        elif doc_type in (5, 6):
            dtip.gCamNCDE = TgCamNCDE(
                iMotEmi=self.data.get("motivoEmision", 1),
            )

        # Nota de remisión (tipo 7)
        elif doc_type == 7:
            remision = self.data.get("remision", {})
            dtip.gCamNRE = TgCamNRE(
                iMotEmiNR=remision.get("motivo", 1),
            )

        # Items
        dtip.gCamItem = self._build_gCamItems()

        return dtip

    def _build_gCamItems(self) -> list:
        """Grupo E8: Invoice line items."""
        items = []
        for item_data in self.data.get("items", []):
            item = TgCamItem(
                dCodInt=item_data.get("codigo", ""),
                dDesProSer=item_data.get("descripcion", ""),
                cUniMed=item_data.get("unidadMedida", 77),
                dCantProSer=item_data.get("cantidad", 1),
                dInAfIVA=item_data.get("ivaTipo", 1),
                dPropIVA=item_data.get("ivaBase", 100),
                dTasaIVA=item_data.get("iva", 10),
                dBasGravIVA=item_data.get("baseGravada", 0),
                dLiqIVAItem=item_data.get("liquidacionIva", 0),
                dPUniProSer=item_data.get("precioUnitario", 0),
            )
            if item_data.get("ncm"):
                item.dNCM = item_data["ncm"]
            items.append(item)
        return items

    def _build_gTotSub(self) -> TgTotSub:
        """Grupo F: Totals."""
        totales = self.data.get("totales", {})
        return TgTotSub(
            dSubExe=totales.get("totalExento", 0),
            dSub5=totales.get("totalGravado5", 0),
            dSub10=totales.get("totalGravado10", 0),
            dTotOpe=totales.get("totalOperacion", 0),
            dTotIVA=totales.get("totalIva", 0),
            dLiqTotIVA5=totales.get("liquidacionIva5", 0),
            dLiqTotIVA10=totales.get("liquidacionIva10", 0),
            dBaseGrav5=totales.get("baseGravada5", 0),
            dBaseGrav10=totales.get("baseGravada10", 0),
            dTBasGraIVA=totales.get("totalBaseGravada", 0),
            dTotGralOpe=totales.get("totalPYG", 0),
        )

    def _build_gCamCond(self) -> TgCamCond:
        """Grupo G: Payment condition."""
        cond = self.data.get("condicion", {})
        return TgCamCond(
            iCondOpe=cond.get("tipo", 1),
        )

    def _build_gCamDEAsoc(self, docs: list) -> list:
        """Grupo H: Associated documents."""
        result = []
        for doc in docs:
            assoc = TgCamDEAsoc(
                iTipDocAso=doc.get("tipoAsociacion", 1),
            )
            if doc.get("cdc"):
                assoc.dCdCDERef = doc["cdc"]
            if doc.get("timbrado"):
                assoc.dNTimDI = doc["timbrado"]
            if doc.get("establecimiento"):
                assoc.dEstDocAso = doc["establecimiento"]
            if doc.get("punto"):
                assoc.dPExpDocAso = doc["punto"]
            if doc.get("numero"):
                assoc.dNumDocAso = doc["numero"]
            if doc.get("fecha"):
                assoc.dFecEmiDI = doc["fecha"]
            result.append(assoc)
        return result
