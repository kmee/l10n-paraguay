# l10n_py_account_batch_payment_iso20022/models/account_batch_payment.py

import base64

from odoo import fields, models

# Categoría de propósito de la transferencia (BCP SIPAP): distingue el
# canal SPI (Sistema de Pagos Inmediatos, bajo valor) del canal LBTR
# (Liquidación Bruta en Tiempo Real, alto valor / moneda extranjera).
#
# NOTA: "SPI"/"LBTR" no son códigos del catálogo externo estándar ISO 20022
# (ExternalCategoryPurpose1Code); son la nomenclatura propia del BCP para
# sus dos canales de liquidación. Por eso se informan en
# `PmtTpInf/CtgyPurp/Prtry` (código propietario), no en `CtgyPurp/Cd`
# (reservado a códigos del catálogo externo ISO). Cada banco receptor debe
# confirmar si esperan este valor en `Prtry` o en otro punto del mensaje.
L10N_PY_ISO20022_CATEGORY_SPI = "SPI"
L10N_PY_ISO20022_CATEGORY_LBTR = "LBTR"

PAIN_001_NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def _l10n_py_iso20022_category_purpose(self, amount, currency):
        """Determina si un pago va por el canal SPI o LBTR.

        El corte (umbral) se lee de `res.company` (ver
        `l10n_py_iso20022_spi_lbtr_threshold`) en lugar de estar
        hardcodeado, precisamente porque el valor real no está confirmado
        con el BCP (ver advertencia en el campo y en el README de este
        módulo). También se considera LBTR cualquier pago en moneda
        distinta a la de la empresa, siguiendo la definición funcional de
        LBTR (alto valor **o** moneda extranjera).
        """
        self.ensure_one()
        company = self.journal_id.company_id
        if currency and company.currency_id and currency != company.currency_id:
            return L10N_PY_ISO20022_CATEGORY_LBTR
        threshold = company.l10n_py_iso20022_spi_lbtr_threshold
        if threshold and amount >= threshold:
            return L10N_PY_ISO20022_CATEGORY_LBTR
        return L10N_PY_ISO20022_CATEGORY_SPI

    def _l10n_py_iso20022_build_document(self):
        """Construye el árbol lxml del mensaje pain.001.001.09.

        Import diferido de `lxml.etree` (mismo patrón usado en
        `l10n_py_edi_sifen/models/edi_connector.py`) para no forzar la
        dependencia al importar el módulo si en algún momento no se llega
        a ejecutar este método.
        """
        from lxml import etree

        self.ensure_one()
        company = self.journal_id.company_id
        journal_bank = self.journal_id.bank_account_id
        payments = self.payment_ids
        currency = self.journal_id.currency_id or company.currency_id
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())

        total_amount = sum(payments.mapped("amount"))
        ctrl_sum = f"{total_amount:.2f}"
        nb_of_txs = str(len(payments))

        document = etree.Element(
            "Document",
            nsmap={None: PAIN_001_NAMESPACE},
        )
        cstmr_cdt_trf_initn = etree.SubElement(document, "CstmrCdtTrfInitn")

        # --- GrpHdr ---
        grp_hdr = etree.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
        etree.SubElement(grp_hdr, "MsgId").text = f"SIPAP-{self.id}-{self.name or ''}"[
            :35
        ]
        etree.SubElement(grp_hdr, "CreDtTm").text = now.isoformat()
        etree.SubElement(grp_hdr, "NbOfTxs").text = nb_of_txs
        etree.SubElement(grp_hdr, "CtrlSum").text = ctrl_sum
        initg_pty = etree.SubElement(grp_hdr, "InitgPty")
        etree.SubElement(initg_pty, "Nm").text = (company.name or "")[:140]

        # --- PmtInf (un único bloque de pago por lote) ---
        pmt_inf = etree.SubElement(cstmr_cdt_trf_initn, "PmtInf")
        etree.SubElement(pmt_inf, "PmtInfId").text = f"PMT-{self.id}"[:35]
        etree.SubElement(pmt_inf, "PmtMtd").text = "TRF"
        etree.SubElement(pmt_inf, "NbOfTxs").text = nb_of_txs
        etree.SubElement(pmt_inf, "CtrlSum").text = ctrl_sum

        # PmtTpInf/CtgyPurp: distinción SPI vs. LBTR. Se informa a nivel de
        # PmtInf (todo el lote), no por transacción individual: si un lote
        # mezclara pagos SPI y LBTR sería responsabilidad de un módulo
        # exportador más específico separar los lotes; este exportador
        # genérico clasifica el lote completo según su monto/moneda total.
        pmt_tp_inf = etree.SubElement(pmt_inf, "PmtTpInf")
        ctgy_purp = etree.SubElement(pmt_tp_inf, "CtgyPurp")
        etree.SubElement(
            ctgy_purp, "Prtry"
        ).text = self._l10n_py_iso20022_category_purpose(total_amount, currency)

        etree.SubElement(pmt_inf, "ReqdExctnDt").text = fields.Date.to_string(
            fields.Date.context_today(self)
        )

        dbtr = etree.SubElement(pmt_inf, "Dbtr")
        etree.SubElement(dbtr, "Nm").text = (company.name or "")[:140]

        dbtr_acct = etree.SubElement(pmt_inf, "DbtrAcct")
        dbtr_acct_id = etree.SubElement(dbtr_acct, "Id")
        _append_othr_id(
            etree, dbtr_acct_id, journal_bank.acc_number if journal_bank else ""
        )

        dbtr_agt = etree.SubElement(pmt_inf, "DbtrAgt")
        dbtr_agt_fin_instn_id = etree.SubElement(dbtr_agt, "FinInstnId")
        bank = self._l10n_py_get_batch_export_bank()
        _append_othr_id(
            etree, dbtr_agt_fin_instn_id, bank.l10n_py_sipap_code if bank else ""
        )

        for payment in payments:
            self._l10n_py_iso20022_append_credit_transfer(etree, pmt_inf, payment)

        return document

    def _l10n_py_iso20022_append_credit_transfer(self, etree, pmt_inf, payment):
        """Agrega un bloque `CdtTrfTxInf` correspondiente a un pago del lote."""
        partner_bank = payment.partner_bank_id
        currency = payment.currency_id

        cdt_trf_tx_inf = etree.SubElement(pmt_inf, "CdtTrfTxInf")

        pmt_id = etree.SubElement(cdt_trf_tx_inf, "PmtId")
        etree.SubElement(pmt_id, "EndToEndId").text = f"PAY-{payment.id}"[:35]

        amt = etree.SubElement(cdt_trf_tx_inf, "Amt")
        instd_amt = etree.SubElement(amt, "InstdAmt")
        instd_amt.set("Ccy", currency.name if currency else "")
        instd_amt.text = f"{payment.amount:.2f}"

        cdtr_agt = etree.SubElement(cdt_trf_tx_inf, "CdtrAgt")
        cdtr_agt_fin_instn_id = etree.SubElement(cdtr_agt, "FinInstnId")
        _append_othr_id(
            etree,
            cdtr_agt_fin_instn_id,
            partner_bank.bank_id.l10n_py_sipap_code if partner_bank else "",
        )

        cdtr = etree.SubElement(cdt_trf_tx_inf, "Cdtr")
        etree.SubElement(cdtr, "Nm").text = (payment.partner_id.name or "")[:140]

        cdtr_acct = etree.SubElement(cdt_trf_tx_inf, "CdtrAcct")
        cdtr_acct_id = etree.SubElement(cdtr_acct, "Id")
        _append_othr_id(
            etree, cdtr_acct_id, partner_bank.acc_number if partner_bank else ""
        )

        if payment.memo:
            rmt_inf = etree.SubElement(cdt_trf_tx_inf, "RmtInf")
            etree.SubElement(rmt_inf, "Ustrd").text = payment.memo[:140]

    def _l10n_py_export_iso20022(self):
        """Exportador genérico ISO 20022 pain.001.001.09.

        Registrado en `res.bank.l10n_py_batch_export_code` bajo el código
        `iso20022` (ver `res_bank.py`). Sigue el contrato definido por
        `l10n_py_account_batch_payment._l10n_py_generate_batch_file()`:
        retorna un dict `{'file': <base64>, 'filename': <str>}`.

        IMPORTANTE (ver README): este es un exportador de schema ISO 20022
        GENÉRICO. No está confirmado que Bancard/BCP ni ningún banco
        paraguayo particular acepte este layout exacto tal cual; debe
        validarse con el banco receptor antes de usarse en producción.
        """
        self.ensure_one()
        document = self._l10n_py_iso20022_build_document()

        from lxml import etree

        xml_bytes = etree.tostring(
            document, xml_declaration=True, encoding="UTF-8", pretty_print=True
        )
        return {
            "file": base64.b64encode(xml_bytes),
            "filename": f"sipap_iso20022_{self.id}.xml",
        }


def _append_othr_id(etree, parent, identification):
    """Agrega a `parent` un elemento `<Othr><Id>...</Id></Othr>`.

    Se centraliza porque el schema pain.001.001.09 repite el mismo patrón
    `CashAccount40/AccountIdentification4Choice/Othr/GenericAccountIdentification1/Id`
    (o su equivalente `FinancialInstitutionIdentification18/Othr`) en varios
    puntos del mensaje (cuenta del deudor, cuenta del acreedor, agente
    financiero del deudor y del acreedor). Todos identifican mediante
    "Othr" (identificación propietaria/local) en lugar de IBAN/BIC, ya que
    ni las cuentas bancarias paraguayas ni los códigos SIPAP de banco son
    IBAN/BIC.
    """
    othr = etree.SubElement(parent, "Othr")
    etree.SubElement(othr, "Id").text = identification or ""
    return othr
