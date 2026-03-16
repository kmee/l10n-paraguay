# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

"""
RDeBuilder: Converts invoice_data dict → pysifen RDe binding object.

Mapping follows SIFEN v150 Manual Técnico.
"""

import logging
from datetime import datetime
from decimal import Decimal

from pysifen.de.bindings.v150.fe_v141 import (
    RDe,
    TdDcondOpe,
    TdDesAfecIva,
    TdDesIndPresValue,
    TdDesMotEmi,
    TdDesTiDe,
    TdDesTipDocAso,
    TdDesTipEmi,
    TDe,
    TgActEco,
    TgCamCond,
    TgCamDeasoc,
    TgCamFe,
    TgCamFuFd,
    TgCamItem,
    TgCamIva,
    TgCamNcde,
    TgCamNre,
    TgCopeDe,
    TgDaGoc,
    TgDatRec,
    TgDtim,
    TgDtipDe,
    TgEmis,
    TgTotSub,
    TgValorItem,
    TiRespEmiNr,
)
from pysifen.de.bindings.v150.xmldsig_core_schema import (
    CanonicalizationMethod,
    Signature,
    SignatureMethod,
    SignatureValue,
    SignedInfo,
)

_logger = logging.getLogger(__name__)

# === Lookup tables for SIFEN description enums ===

_TIP_EMI_DESC = {1: TdDesTipEmi.NORMAL, 2: TdDesTipEmi.CONTINGENCIA}

_TI_DE_DESC = {
    1: TdDesTiDe.FACTURA_ELECTR_NICA,
    5: TdDesTiDe.NOTA_DE_CR_DITO_ELECTR_NICA,
    6: TdDesTiDe.NOTA_DE_D_BITO_ELECTR_NICA,
}

_IND_PRES_DESC = {
    1: TdDesIndPresValue.OPERACI_N_PRESENCIAL,
    2: TdDesIndPresValue.OPERACI_N_ELECTR_NICA,
    3: TdDesIndPresValue.OPERACI_N_TELEMARKETING,
    4: TdDesIndPresValue.VENTA_A_DOMICILIO,
    5: TdDesIndPresValue.OPERACI_N_BANCARIA,
}

_COND_OPE_DESC = {1: TdDcondOpe.CONTADO, 2: TdDcondOpe.CR_DITO}

_MOT_EMI_DESC = {
    1: TdDesMotEmi.ANULACI_N,
    2: TdDesMotEmi.DEVOLUCI_N,
    3: TdDesMotEmi.DESCUENTO,
    4: TdDesMotEmi.BONIFICACI_N,
    5: TdDesMotEmi.CR_DITO_INCOBRABLE,
    6: TdDesMotEmi.RECUPERO_DE_COSTO,
    7: TdDesMotEmi.RECUPERO_DE_GASTO,
    8: TdDesMotEmi.AJUSTE_DE_PRECIO,
}

_AFEC_IVA_DESC = {
    1: TdDesAfecIva.GRAVADO_IVA,
    2: TdDesAfecIva.EXONERADO_ART_83_LEY_125_91,
    3: TdDesAfecIva.EXENTO,
    4: TdDesAfecIva.GRAVADO_PARCIAL_GRAV_EXENTO,
}

_TIP_DOC_ASO_DESC = {
    1: TdDesTipDocAso.ELECTR_NICO,
    2: TdDesTipDocAso.IMPRESO,
}


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
            dDVId=self.cdc[-1] if len(self.cdc) == 43 else "",
            dFecFirma="",
            gOpeDE=self._build_gOpeDE(),
            gTimb=self._build_gTimb(),
            gDatGralOpe=self._build_gDatGralOpe(),
            gDtipDE=self._build_gDtipDE(),
            gTotSub=self._build_gTotSub(),
        )

        # Optional: associated documents (Grupo H)
        assoc_docs = self.data.get("documentosAsociados", [])
        if assoc_docs:
            tde.gCamDEAsoc = self._build_gCamDEAsoc(assoc_docs)

        # Signature and gCamFuFD are required by the binding but filled
        # by pysifen at signing time.  For preview we use empty placeholders.
        empty_signature = Signature(
            SignedInfo=SignedInfo(
                CanonicalizationMethod=CanonicalizationMethod(Algorithm=""),
                SignatureMethod=SignatureMethod(Algorithm=""),
            ),
            SignatureValue=SignatureValue(),
        )
        return RDe(
            dVerFor="150",
            DE=tde,
            Signature=empty_signature,
            gCamFuFD=TgCamFuFd(dCarQR=""),
        )

    def _build_gOpeDE(self) -> TgCopeDe:
        """Grupo A: Operational data."""
        tip_emi = self.data.get("tipoEmision", 1)
        return TgCopeDe(
            iTipEmi=tip_emi,
            dDesTipEmi=_TIP_EMI_DESC.get(tip_emi, TdDesTipEmi.NORMAL),
            dCodSeg=self.data.get("codigoSeguridadAleatorio", "000000000"),
        )

    def _build_gTimb(self) -> TgDtim:
        """Grupo B: Timbrado / document identification."""
        ti_de = self.data.get("tipoDocumento", 1)
        return TgDtim(
            iTiDE=ti_de,
            dDesTiDE=_TI_DE_DESC.get(ti_de, TdDesTiDe.FACTURA_ELECTR_NICA),
            dNumTim=self.data.get("timbrado", ""),
            dEst=self.data.get("establecimiento", "001"),
            dPunExp=self.data.get("punto", "001"),
            dNumDoc=self.data.get("numero", "0000001"),
            dFeIniT=self.data.get("timbradoFechaInicio", ""),
            dFeFinT=self.data.get("timbradoFechaFin", ""),
        )

    def _build_gDatGralOpe(self) -> TgDaGoc:
        """Grupo C: General operation data."""
        fecha_str = self.data.get("fecha", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        return TgDaGoc(
            dFeEmiDE=fecha_str,
            gEmis=self._build_gEmis(),
            gDatRec=self._build_gDatRec(),
        )

    def _build_gEmis(self) -> TgEmis:
        """Grupo D: Emitter (company) data."""
        return TgEmis(
            dRucEm=self.company.get("ruc", ""),
            dDVEmi=self.company.get("dv", ""),
            iTipCont=self.company.get("tipoContribuyente", "2"),
            dNomEmi=self.company.get("razonSocial", ""),
            dNomFanEmi=self.company.get("nombreFantasia", ""),
            dDirEmi=self.company.get("direccion", ""),
            dNumCas=int(self.company.get("numeroCasa", 0)),
            cDepEmi=self.company.get("departamento", 1),
            dDesDepEmi=self.company.get("departamentoDescripcion", ""),
            cDisEmi=str(self.company.get("distrito", 0)) or None,
            cCiuEmi=str(self.company.get("ciudad", "")),
            dDesCiuEmi=self.company.get("ciudadDescripcion", ""),
            dTelEmi=self.company.get("telefono", ""),
            dEmailE=self.company.get("email", ""),
            gActEco=[
                TgActEco(
                    cActEco=self.company.get("actividadEconomicaCodigo", ""),
                    dDesActEco=self.company.get("actividadEconomica", ""),
                )
            ],
        )

    def _build_gDatRec(self) -> TgDatRec:
        """Grupo D: Receiver (customer) data."""
        cliente = self.data.get("cliente", {})
        rec = TgDatRec(
            iNatRec=cliente.get("naturalezaReceptor", "1"),
            iTiOpe=cliente.get("tipoOperacion", "1"),
            cPaisRec=cliente.get("pais", "PRY"),
            dDesPaisRe=cliente.get("paisDescripcion", "Paraguay"),
            dNomRec=cliente.get("razonSocial", ""),
            dNomFanRec=cliente.get("nombreFantasia", ""),
            dDirRec=cliente.get("direccion", ""),
        )
        if cliente.get("ruc"):
            rec.dRucRec = cliente["ruc"]
        if cliente.get("dvReceptor"):
            rec.dDVRec = cliente["dvReceptor"]
        if cliente.get("tipoContribuyente"):
            rec.iTiContRec = cliente["tipoContribuyente"]
        if cliente.get("departamento"):
            rec.cDepRec = cliente["departamento"]
        if cliente.get("ciudad"):
            rec.cCiuRec = cliente["ciudad"]
        if cliente.get("email"):
            rec.dEmailRec = cliente["email"]
        if cliente.get("telefono"):
            rec.dTelRec = cliente["telefono"]
        if cliente.get("celular"):
            rec.dCelRec = cliente["celular"]
        if cliente.get("documentoTipo"):
            rec.iTipIDRec = str(cliente["documentoTipo"])
        if cliente.get("documentoNumero"):
            rec.dNumIDRec = cliente["documentoNumero"]
        return rec

    def _build_gDtipDE(self) -> TgDtipDe:
        """Grupo E: Document type specifics + items."""
        dtip = TgDtipDe()

        doc_type = self.data.get("tipoDocumento", 1)

        # Factura electrónica (tipo 1) or Autofactura (tipo 4)
        if doc_type in (1, 4):
            factura = self.data.get("factura", {})
            presencia = factura.get("presencia", 1)
            dtip.gCamFE = TgCamFe(
                iIndPres=presencia,
                dDesIndPres=_IND_PRES_DESC.get(
                    presencia, TdDesIndPresValue.OPERACI_N_PRESENCIAL
                ),
            )

        # Nota de crédito (tipo 5) or Nota de débito (tipo 6)
        elif doc_type in (5, 6):
            mot_emi = self.data.get("motivoEmision", 1)
            dtip.gCamNCDE = TgCamNcde(
                iMotEmi=str(mot_emi),
                dDesMotEmi=_MOT_EMI_DESC.get(mot_emi, TdDesMotEmi.ANULACI_N),
            )

        # Nota de remisión (tipo 7)
        elif doc_type == 7:
            remision = self.data.get("remision", {})
            dtip.gCamNRE = TgCamNre(
                iMotEmiNR=remision.get("motivo", 1),
                iRespEmiNR=TiRespEmiNr.VALUE_1,
            )

        # Payment condition (lives inside gDtipDE)
        cond = self.data.get("condicion", {})
        cond_ope = cond.get("tipo", 1)
        dtip.gCamCond = TgCamCond(
            iCondOpe=cond_ope,
            dDCondOpe=_COND_OPE_DESC.get(cond_ope, TdDcondOpe.CONTADO),
        )

        # Items
        dtip.gCamItem = self._build_gCamItems()

        return dtip

    def _build_gCamItems(self) -> list:
        """Grupo E8: Invoice line items."""
        items = []
        for item_data in self.data.get("items", []):
            iva_tipo = item_data.get("ivaTipo", 1)
            iva_rate = item_data.get("iva", 10)
            base_gravada = Decimal(str(item_data.get("baseGravada", 0)))
            liquidacion_iva = Decimal(str(item_data.get("liquidacionIva", 0)))
            precio = Decimal(str(item_data.get("precioUnitario", 0)))
            cantidad = Decimal(str(item_data.get("cantidad", 1)))
            total_item = precio * cantidad

            item = TgCamItem(
                dCodInt=item_data.get("codigo", ""),
                dDesProSer=item_data.get("descripcion", ""),
                cUniMed=item_data.get("unidadMedida", 77),
                dDesUniMed="UNI",
                dCantProSer=cantidad,
                gValorItem=TgValorItem(
                    dPUniProSer=precio,
                    dDescItem=Decimal("0"),
                    dTotOpeItem=total_item,
                ),
                gCamIVA=TgCamIva(
                    iAfecIVA=iva_tipo,
                    dDesAfecIVA=_AFEC_IVA_DESC.get(iva_tipo, TdDesAfecIva.GRAVADO_IVA),
                    dPropIVA=item_data.get("ivaBase", 100),
                    dTasaIVA=iva_rate,
                    dBasGravIVA=base_gravada,
                    dLiqIVAItem=liquidacion_iva,
                ),
            )
            if item_data.get("ncm"):
                item.dNCM = item_data["ncm"]
            items.append(item)
        return items

    def _build_gTotSub(self) -> TgTotSub:
        """Grupo F: Totals."""
        totales = self.data.get("totales", {})
        return TgTotSub(
            dSubExe=Decimal(str(totales.get("totalExento", 0))),
            dSub5=Decimal(str(totales.get("totalGravado5", 0))),
            dSub10=Decimal(str(totales.get("totalGravado10", 0))),
            dTotOpe=Decimal(str(totales.get("totalOperacion", 0))),
            dTotDesc=Decimal("0"),
            dPorcDescTotal=Decimal("0"),
            dDescTotal=Decimal("0"),
            dAnticipo=Decimal("0"),
            dRedon=Decimal("0"),
            dTotGralOpe=Decimal(str(totales.get("totalPYG", 0))),
            dTotIVA=Decimal(str(totales.get("totalIva", 0))),
            dIVA5=Decimal(str(totales.get("liquidacionIva5", 0))),
            dIVA10=Decimal(str(totales.get("liquidacionIva10", 0))),
            dBaseGrav5=Decimal(str(totales.get("baseGravada5", 0))),
            dBaseGrav10=Decimal(str(totales.get("baseGravada10", 0))),
            dTBasGraIVA=Decimal(str(totales.get("totalBaseGravada", 0))),
        )

    def _build_gCamDEAsoc(self, docs: list) -> list:
        """Grupo H: Associated documents."""
        result = []
        for doc in docs:
            tip_doc_aso = doc.get("tipoAsociacion", 1)
            assoc = TgCamDeasoc(
                iTipDocAso=tip_doc_aso,
                dDesTipDocAso=_TIP_DOC_ASO_DESC.get(
                    tip_doc_aso, TdDesTipDocAso.ELECTR_NICO
                ),
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
