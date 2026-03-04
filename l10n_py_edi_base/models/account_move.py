# l10n_py_edi_base/models/account_move.py

import logging
import secrets
import string

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    # ============== CAMPOS EDI PARAGUAY ==============

    l10n_py_emission_type = fields.Selection(
        [("1", "Normal"), ("2", "Contingencia")],
        string="Tipo de Emisión",
        default="1",
        required=True,
    )

    l10n_py_transaction_type = fields.Selection(
        [
            ("1", "Venta de mercadería"),
            ("2", "Prestación de servicios"),
            ("3", "Mixto (Venta de mercadería y servicios)"),
            ("4", "Venta de activo fijo"),
            ("5", "Venta de divisas"),
            ("6", "Compra de divisas"),
            ("7", "Promoción o entrega de muestras"),
            ("8", "Donación"),
            ("9", "Anticipo"),
            ("10", "Compra de productos"),
            ("11", "Compra de servicios"),
            ("12", "Venta de crédito fiscal"),
            ("13", "Compra de crédito fiscal"),
        ],
        string="Tipo de Transacción",
        required=True,
        default="1",
    )

    l10n_py_presence_type = fields.Selection(
        [
            ("1", "Operación presencial"),
            ("2", "Operación electrónica"),
            ("3", "Operación telemarketing"),
            ("4", "Venta a domicilio"),
            ("5", "Operación bancaria"),
        ],
        string="Tipo de Presencia",
        default="1",
    )

    # Campos de respuesta EDI
    l10n_py_cdc = fields.Char(
        "CDC",
        readonly=True,
        copy=False,
        help="Código de Control del documento electrónico",
    )
    l10n_py_qr_code = fields.Binary("Código QR", readonly=True, copy=False)
    l10n_py_qr_string = fields.Char("String QR", readonly=True, copy=False)
    l10n_py_edi_xml = fields.Binary("XML Firmado", readonly=True, copy=False)
    l10n_py_edi_xml_filename = fields.Char("XML Filename", readonly=True)
    l10n_py_kude_pdf = fields.Binary("KUDE (PDF)", readonly=True, copy=False)
    l10n_py_kude_filename = fields.Char("KUDE Filename", readonly=True)

    l10n_py_edi_status = fields.Selection(
        [
            ("draft", "Borrador"),
            ("to_send", "Para Enviar"),
            ("sent", "Enviado"),
            ("processing", "Procesando"),
            ("accepted", "Aceptado"),
            ("rejected", "Rechazado"),
            ("cancelled", "Cancelado"),
            ("error", "Error"),
        ],
        string="Estado EDI",
        default="draft",
        readonly=True,
        copy=False,
    )

    l10n_py_edi_message = fields.Text("Mensaje EDI", readonly=True, copy=False)
    l10n_py_edi_batch_id = fields.Char("ID de Lote", readonly=True, copy=False)
    l10n_py_security_code = fields.Char(
        "Código de Seguridad", size=9, readonly=True, copy=False
    )
    l10n_py_receipt_id = fields.Char("Receipt ID", help="ID único del sistema cliente")

    # Campos para contingencia
    l10n_py_contingency_motive = fields.Char("Motivo de Contingencia")

    # Documentos asociados (Grupo H SIFEN)
    l10n_py_associated_document_ids = fields.One2many(
        "l10n_py.associated.document",
        "move_id",
        string="Documentos Asociados",
        help="Documentos asociados al DTE (Grupo H del SIFEN)",
    )

    # Campos NRE (Nota de Remisión Electrónica — tipo 7)
    l10n_py_nre_motive = fields.Selection(
        [
            ("1", "Traslado por venta"),
            ("2", "Traslado por consignación"),
            ("3", "Traslado por exportación"),
            ("4", "Traslado por importación"),
            ("5", "Traslado entre locales"),
            ("6", "Otros"),
        ],
        string="Motivo de Remisión (E501)",
    )

    l10n_py_nre_estimated_invoice_date = fields.Date(
        string="Fecha Estimada de Facturación (E506)",
        help="Fecha estimada de facturación para NRE sin factura asociada",
    )

    # Campo prazo de transmissão
    l10n_py_transmission_deadline = fields.Datetime(
        string="Plazo de Transmisión",
        compute="_compute_transmission_deadline",
        store=True,
        help="Plazo máximo para transmitir el DTE (72 horas desde emisión)",
    )

    # ============== LIFECYCLE METHODS ==============

    def action_post(self):
        """Override para configurar estado EDI al confirmar factura."""
        res = super().action_post()
        for move in self:
            if move.move_type in ("out_invoice", "out_refund"):
                move.l10n_py_edi_status = "to_send"
        return res

    @api.depends("invoice_date")
    def _compute_transmission_deadline(self):
        """Calcular plazo máximo de transmisión (72h desde emisión)"""
        for move in self:
            if move.invoice_date:
                # 72 horas desde el inicio del día de emisión
                move.l10n_py_transmission_deadline = fields.Datetime.from_string(
                    str(move.invoice_date) + " 00:00:00"
                ) + relativedelta(hours=72)
            else:
                move.l10n_py_transmission_deadline = False

    # ============== ONCHANGE METHODS ==============

    @api.onchange("invoice_line_ids")
    def _onchange_invoice_lines_transaction_type(self):
        """Auto-detectar tipo de transacción basado en los productos"""
        if self.invoice_line_ids:
            has_products = False
            has_services = False

            for line in self.invoice_line_ids.filtered(lambda l: not l.display_type):
                if line.product_id:
                    if line.product_id.type in ["consu", "product"]:
                        has_products = True
                    elif line.product_id.type == "service":
                        has_services = True

            if has_products and has_services:
                self.l10n_py_transaction_type = "3"  # Mixto
            elif has_services:
                self.l10n_py_transaction_type = "2"  # Servicios
            else:
                self.l10n_py_transaction_type = "1"  # Mercadería

    # ============== CONSTRAINT METHODS ==============

    @api.constrains("l10n_py_security_code")
    def _check_security_code(self):
        for record in self:
            if record.l10n_py_security_code and len(record.l10n_py_security_code) != 9:
                raise ValidationError(
                    _("El código de seguridad debe tener " "exactamente 9 caracteres")
                )

    # ============== PRIVATE METHODS ==============

    def _generate_security_code(self):
        """Generar código de seguridad aleatorio de 9 dígitos"""
        return "".join(secrets.choice(string.digits) for _ in range(9))

    def _prepare_edi_document_data(self):
        """Preparar datos del documento electrónico en formato JSON"""
        self.ensure_one()

        if not self.l10n_py_security_code:
            self.l10n_py_security_code = self._generate_security_code()

        # Obtener código de tipo de documento desde l10n_latam
        doc_type_code = "1"
        if self.l10n_latam_document_type_id:
            doc_type_code = self.l10n_latam_document_type_id.code or "1"

        # Construir estructura de datos según formato requerido
        document_data = {
            "tipoDocumento": int(doc_type_code),
            "establecimiento": (self.journal_id.l10n_py_establishment or "001"),
            "punto": self.journal_id.l10n_py_point or "001",
            "numero": self._get_edi_sequence_number(),
            "descripcion": self.name or "",
            "observacion": self.narration or "",
            "fecha": (
                self.invoice_date.strftime("%Y-%m-%dT%H:%M:%S")
                if self.invoice_date
                else fields.Datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            ),
            "tipoEmision": int(self.l10n_py_emission_type),
            "tipoTransaccion": int(self.l10n_py_transaction_type),
            "tipoImpuesto": 1,  # IVA
            "moneda": self.currency_id.name,
            "receiptId": (self.l10n_py_receipt_id or f"{self.company_id.id}-{self.id}"),
            "codigoSeguridadAleatorio": self.l10n_py_security_code,
            "cliente": self._prepare_customer_data(),
            "factura": {"presencia": int(self.l10n_py_presence_type)},
            "condicion": self._prepare_payment_condition(),
            "items": self._prepare_invoice_lines(),
        }

        # Agregar datos de usuario emisor si existe
        if self.user_id:
            document_data["usuario"] = {
                "documentoTipo": 1,  # Cédula
                "documentoNumero": self.user_id.partner_id.vat or "",
                "nombre": self.user_id.name,
                "cargo": self.user_id.function or "Vendedor",
            }

        # Documentos asociados (Grupo H)
        if self.l10n_py_associated_document_ids:
            document_data["documentosAsociados"] = self._prepare_associated_documents()

        # Campos NRE (tipo=7)
        doc_type_code = "1"
        if self.l10n_latam_document_type_id:
            doc_type_code = self.l10n_latam_document_type_id.code or "1"
        if doc_type_code == "7":
            document_data["remision"] = {
                "motivo": int(self.l10n_py_nre_motive or "1"),
            }
            if self.l10n_py_nre_estimated_invoice_date:
                document_data["remision"][
                    "fechaEstimada"
                ] = self.l10n_py_nre_estimated_invoice_date.strftime("%Y-%m-%d")

        # Totales SIFEN
        document_data["totales"] = {
            "totalExento": self.l10n_py_amount_exempt,  # F003
            "totalGravado5": self.l10n_py_amount_subtotal_5,  # F004
            "totalGravado10": self.l10n_py_amount_subtotal_10,  # F005
            "totalOperacion": self.l10n_py_total_operation,  # F008
            "totalIva": self.l10n_py_amount_iva_total,  # F014
            "liquidacionIva5": self.l10n_py_amount_iva_5,  # F015
            "liquidacionIva10": self.l10n_py_amount_iva_10,  # F016
            "baseGravada5": self.l10n_py_base_5,  # F018
            "baseGravada10": self.l10n_py_base_10,  # F019
            "totalBaseGravada": self.l10n_py_base_total,  # F020
        }
        if self.l10n_py_amount_total_pyg:
            document_data["totales"]["totalPYG"] = self.l10n_py_amount_total_pyg  # F023

        return document_data

    def _prepare_associated_documents(self):
        """Preparar datos de documentos asociados para JSON EDI."""
        docs = []
        for ad in self.l10n_py_associated_document_ids:
            doc_data = {
                "tipoAsociacion": int(ad.association_type),
            }
            if ad.association_type == "1":
                doc_data["cdc"] = ad.cdc
            elif ad.association_type == "2":
                doc_data.update(
                    {
                        "timbrado": ad.timbrado,
                        "establecimiento": ad.establishment,
                        "punto": ad.expedition_point,
                        "numero": ad.doc_number,
                        "tipoDocumentoImpreso": int(ad.doc_type_code),
                        "fecha": (
                            ad.doc_date.strftime("%Y-%m-%d") if ad.doc_date else ""
                        ),
                    }
                )
            elif ad.association_type == "3":
                doc_data.update(
                    {
                        "constanciaTipo": int(ad.constancia_type),
                        "constanciaNumero": ad.constancia_number,
                    }
                )
            docs.append(doc_data)
        return docs

    def _prepare_customer_data(self):
        """Preparar datos del cliente"""
        partner = self.partner_id

        customer_data = {
            "contribuyente": partner.l10n_py_taxpayer_type == "1",
            "ruc": partner.l10n_py_ruc or "",
            "razonSocial": partner.name,
            "nombreFantasia": partner.l10n_py_fantasy_name or partner.name,
            "tipoOperacion": 1,  # B2B
            "direccion": partner.street or "N/A",
            "numeroCasa": (
                partner.street_number if hasattr(partner, "street_number") else "0"
            )
            or "0",
            "pais": partner.country_id.code or "PRY",
            "paisDescripcion": partner.country_id.name or "Paraguay",
        }

        # Agregar datos de ubicación si están disponibles
        if partner.l10n_py_department_code:
            customer_data.update(
                {
                    "departamento": partner.l10n_py_department_code,
                    "departamentoDescripcion": (
                        partner.state_id.name if partner.state_id else ""
                    ),
                    "ciudad": partner.l10n_py_city_code or "",
                    "ciudadDescripcion": partner.city or "",
                }
            )

        # Agregar contacto
        if partner.phone or partner.mobile:
            customer_data["telefono"] = partner.phone or ""
            customer_data["celular"] = partner.mobile or ""

        if partner.email:
            customer_data["email"] = partner.email

        # Tipo y número de documento
        if partner.l10n_py_taxpayer_type:
            customer_data["tipoContribuyente"] = 1 if partner.is_company else 2

        # No-contribuyente: incluir documento de identidad (D024/D025)
        if partner.l10n_py_taxpayer_type == "2":
            if partner.l10n_py_doc_type:
                customer_data["documentoTipo"] = int(partner.l10n_py_doc_type)
            if partner.l10n_py_doc_number:
                customer_data["documentoNumero"] = partner.l10n_py_doc_number

        return customer_data

    def _prepare_payment_condition(self):
        """Preparar condición de pago"""
        payment_condition = {
            "tipo": (
                2 if self.invoice_payment_term_id else 1
            ),  # 1: Contado, 2: Crédito
        }

        if self.invoice_payment_term_id:
            # Es crédito
            payment_condition["credito"] = {
                "tipo": 1,  # 1: Plazo, 2: Cuotas
                "plazo": (
                    f"{self.invoice_payment_term_id.line_ids[0].days} días"
                    if self.invoice_payment_term_id.line_ids
                    else "0 días"
                ),
                "cuotas": len(self.invoice_payment_term_id.line_ids),
            }

            # Preparar información de cuotas
            cuotas = []
            if self.invoice_date and self.invoice_payment_term_id.line_ids:
                for line in self.invoice_payment_term_id.line_ids:
                    due_date = self.invoice_date + relativedelta(days=line.days)
                    cuotas.append(
                        {
                            "moneda": self.currency_id.name,
                            "monto": (
                                self.amount_total
                                / len(self.invoice_payment_term_id.line_ids)
                            ),
                            "vencimiento": due_date.strftime("%Y-%m-%d"),
                        }
                    )

            payment_condition["credito"]["infoCuotas"] = cuotas
        else:
            # Es contado
            payment_condition["entregas"] = [
                {
                    "tipo": 1,  # Efectivo
                    "monto": str(self.amount_total),
                    "moneda": self.currency_id.name,
                    "cambio": 0,
                }
            ]

        return payment_condition

    def _prepare_invoice_lines(self):
        """Preparar líneas de la factura"""
        items = []

        for line in self.invoice_line_ids.filtered(lambda l: not l.display_type):
            # Determinar tasa de IVA
            iva_rate = 10  # Por defecto 10%
            iva_type = 1  # Gravado IVA

            for tax in line.tax_ids:
                if tax.amount == 5:
                    iva_rate = 5
                elif tax.amount == 0:
                    iva_type = 3  # Exenta
                    iva_rate = 0

            # Calcular base gravable e liquidação IVA por linha (SIFEN)
            base_gravada = 0.0
            liquidacion_iva = 0.0
            if iva_rate > 0 and line.price_total:
                base_gravada = line.price_total / (1 + iva_rate / 100)
                liquidacion_iva = line.price_total - base_gravada

            item = {
                "codigo": (
                    line.product_id.default_code or f"PROD-{line.product_id.id}"
                ),
                "descripcion": line.name or line.product_id.name,
                "observacion": "",
                "ncm": (
                    line.product_id.l10n_py_ncm_code
                    if hasattr(line.product_id, "l10n_py_ncm_code")
                    else ""
                )
                or "",
                "unidadMedida": 77,  # UNI - Unidad
                "cantidad": line.quantity,
                "precioUnitario": line.price_unit,
                "cambio": 0,
                "ivaTipo": iva_type,
                "ivaBase": 100,
                "iva": iva_rate,
                "baseGravada": round(base_gravada, 2),
                "liquidacionIva": round(liquidacion_iva, 2),
                "lote": "",
                "vencimiento": "",
            }

            items.append(item)

        return items

    def _get_edi_sequence_number(self):
        """Obtener número de secuencia para EDI"""
        if self.l10n_py_invoice_number:
            return str(self.l10n_py_invoice_number).zfill(7)
        if self.name:
            number = "".join(filter(str.isdigit, self.name.split("/")[-1]))
            return number.zfill(7)[-7:]
        return "0000001"

    def _validate_edi_document_type(self):
        """Validar requisitos específicos por tipo de DTE.

        Llamado antes del envío EDI. Retorna lista de errores.
        """
        errors = []
        code = (
            self.l10n_latam_document_type_id.code
            if self.l10n_latam_document_type_id
            else ""
        )
        docs = self.l10n_py_associated_document_ids

        # AFE (code=4): exatamente 1 constância
        if code == "4":
            if len(docs) != 1:
                errors.append(
                    _("Autofactura: debe tener exactamente 1 documento asociado.")
                )
            elif docs[0].association_type != "3":
                errors.append(
                    _(
                        "Autofactura: el documento asociado debe "
                        "ser una constancia electrónica."
                    )
                )

        # NCE (code=5): exatamente 1 doc associado
        elif code == "5":
            if len(docs) != 1:
                errors.append(
                    _(
                        "Nota de Crédito Electrónica: debe tener "
                        "exactamente 1 documento asociado."
                    )
                )

        # NDE (code=6): exatamente 1 doc associado
        elif code == "6":
            if len(docs) != 1:
                errors.append(
                    _(
                        "Nota de Débito Electrónica: debe tener "
                        "exactamente 1 documento asociado."
                    )
                )

        # NRE (code=7): validações NRE
        elif code == "7":
            if not self.l10n_py_nre_motive:
                errors.append(_("Nota de Remisión: el motivo es obligatorio."))
            # Motivo "1" (traslado por venta) sin doc asociado → requer data estimada
            if self.l10n_py_nre_motive == "1" and not docs:
                if not self.l10n_py_nre_estimated_invoice_date:
                    errors.append(
                        _(
                            "NRE traslado por venta sin documento "
                            "asociado: debe indicar fecha estimada "
                            "de facturación."
                        )
                    )
            # Data estimada no puede exceder el mes de emisión
            if self.l10n_py_nre_estimated_invoice_date and self.invoice_date:
                est_date = self.l10n_py_nre_estimated_invoice_date
                inv_date = self.invoice_date
                # La fecha estimada no debe superar el mes siguiente
                if est_date.month > inv_date.month + 1 or (
                    est_date.year > inv_date.year
                    and not (inv_date.month == 12 and est_date.month == 1)
                ):
                    errors.append(
                        _(
                            "La fecha estimada de facturación no puede "
                            "exceder el mes siguiente al de emisión."
                        )
                    )
            # Motivo "5" (entre locales) → RUC receptor = RUC emissor
            if self.l10n_py_nre_motive == "5":
                partner_ruc = self.partner_id.l10n_py_ruc or ""
                company_ruc = self.company_id.l10n_py_ruc or ""
                if partner_ruc != company_ruc:
                    errors.append(
                        _(
                            "Traslado entre locales: el RUC del "
                            "receptor debe coincidir con el del emisor."
                        )
                    )

        return errors

    def _validate_edi_data(self):
        """Validar datos antes de enviar a EDI"""
        errors = []

        # Validar datos de la empresa
        company = self.company_id
        if not company.l10n_py_ruc:
            errors.append(_("Configure el RUC de la empresa"))

        # Validar datos del cliente (F15)
        partner = self.partner_id
        if partner.l10n_py_taxpayer_type == "1" and not partner.l10n_py_ruc:
            errors.append(_("El cliente contribuyente debe tener RUC"))
        if partner.l10n_py_taxpayer_type == "2" and not partner.l10n_py_doc_number:
            errors.append(
                _(
                    "El cliente no contribuyente debe tener número "
                    "de documento de identidad"
                )
            )

        if not partner.street:
            errors.append(_("La dirección del cliente es obligatoria"))

        # Validar datos del diario
        journal = self.journal_id
        if not journal.l10n_py_authorization_id:
            errors.append(_("Configure el timbrado en el diario"))

        if (
            journal.l10n_py_authorization_validity
            and journal.l10n_py_authorization_validity < fields.Date.today()
        ):
            errors.append(_("El timbrado está vencido"))

        # Validar productos
        for line in self.invoice_line_ids.filtered(lambda l: not l.display_type):
            if hasattr(line.product_id, "l10n_py_ncm_code"):
                if not line.product_id.l10n_py_ncm_code:
                    errors.append(
                        _("El producto %s no tiene código NCM") % line.product_id.name
                    )

        # Validar requisitos por tipo de documento (F03-F07)
        errors.extend(self._validate_edi_document_type())

        if errors:
            raise UserError("\n".join(errors))

        return True

    # ============== PUBLIC METHODS ==============

    def action_send_edi(self):
        """Enviar documento a sistema EDI"""
        self.ensure_one()

        # Validar datos
        self._validate_edi_data()

        # Preparar datos
        document_data = self._prepare_edi_document_data()

        # Obtener conector configurado
        provider = (
            self.env["ir.config_parameter"].sudo().get_param("l10n_py.edi_provider")
        )

        if provider == "factpy":
            connector = (
                self.env["l10n_py.edi.connector.factpy"].sudo().search([], limit=1)
            )
        elif provider == "facturasend":
            connector = (
                self.env["l10n_py.edi.connector.facturasend"].sudo().search([], limit=1)
            )
        else:
            raise UserError(_("No hay un proveedor EDI configurado"))

        if not connector:
            raise UserError(_("No se encontró un conector EDI configurado"))

        try:
            # Enviar documento
            self.l10n_py_edi_status = "sent"
            response = connector.send_document(document_data)

            # Procesar respuesta
            if response.get("success"):
                self._process_edi_response(response)
            else:
                self.l10n_py_edi_status = "rejected"
                self.l10n_py_edi_message = response.get("error", "Error desconocido")

        except Exception as e:
            _logger.error("Error enviando EDI: %s", str(e))
            self.l10n_py_edi_status = "error"
            self.l10n_py_edi_message = str(e)
            raise UserError(_("Error enviando documento: %s") % str(e)) from e

    def _process_edi_response(self, response):
        """Procesar respuesta exitosa del EDI"""
        self.ensure_one()

        result = response.get("result", {})

        # Guardar CDC y otros datos
        if result.get("deList"):
            de_data = result["deList"][0]
            self.write(
                {
                    "l10n_py_cdc": de_data.get("cdc"),
                    "l10n_py_qr_string": de_data.get("qr"),
                    "l10n_py_edi_status": "accepted",
                    "l10n_py_edi_batch_id": result.get("loteId"),
                    "l10n_py_edi_message": ("Documento aceptado exitosamente"),
                }
            )

            # Guardar XML si viene
            if de_data.get("xml"):
                self.l10n_py_edi_xml = de_data["xml"].encode("utf-8")
                self.l10n_py_edi_xml_filename = f"{self.l10n_py_cdc}.xml"

            # Auto-generar KuDE al aceptar
            try:
                self._generate_kude()
            except Exception as e:
                _logger.warning("Error generando KuDE: %s", str(e))

    def action_cancel_edi(self):
        """Cancelar documento electrónico"""
        self.ensure_one()

        if not self.l10n_py_cdc:
            raise UserError(_("No se puede cancelar un documento sin CDC"))

        # Obtener conector
        provider = (
            self.env["ir.config_parameter"].sudo().get_param("l10n_py.edi_provider")
        )

        if provider == "factpy":
            connector = (
                self.env["l10n_py.edi.connector.factpy"].sudo().search([], limit=1)
            )
        elif provider == "facturasend":
            connector = (
                self.env["l10n_py.edi.connector.facturasend"].sudo().search([], limit=1)
            )
        else:
            raise UserError(_("No hay un proveedor EDI configurado"))

        if connector and hasattr(connector, "cancel_document"):
            response = connector.cancel_document(self.l10n_py_cdc)
            if response.get("success"):
                self.l10n_py_edi_status = "cancelled"
                self.l10n_py_edi_message = f"Cancelado el {fields.Datetime.now()}"
            else:
                raise UserError(
                    _("Error cancelando documento: %s") % response.get("error")
                )
        else:
            self.l10n_py_edi_status = "cancelled"
            self.l10n_py_edi_message = f"Cancelado el {fields.Datetime.now()}"

    def action_retry_edi(self):
        """Reintentar envío de documento"""
        self.ensure_one()

        if self.l10n_py_edi_status not in ["error", "rejected"]:
            raise UserError(
                _("Solo se pueden reintentar documentos " "con error o rechazados")
            )

        return self.action_send_edi()

    def action_download_xml(self):
        """Descargar XML del documento"""
        self.ensure_one()

        if not self.l10n_py_edi_xml:
            raise UserError(_("No hay XML disponible para este documento"))

        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/{self._name}/{self.id}/l10n_py_edi_xml/"
                f"{self.l10n_py_edi_xml_filename}?download=true"
            ),
            "target": "self",
        }

    def action_download_kude(self):
        """Descargar KUDE (PDF)"""
        self.ensure_one()

        if not self.l10n_py_kude_pdf:
            # Intentar generar KUDE
            self._generate_kude()

        if not self.l10n_py_kude_pdf:
            raise UserError(_("No hay KUDE disponible para este documento"))

        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/{self._name}/{self.id}/l10n_py_kude_pdf/"
                f"{self.l10n_py_kude_filename}?download=true"
            ),
            "target": "self",
        }

    def _generate_kude(self):
        """Generar KUDE (representación gráfica del documento electrónico)."""
        import base64

        self.ensure_one()
        if not self.l10n_py_cdc:
            return
        report = self.env.ref("l10n_py_edi_base.action_kude_report")
        pdf_content, _ = report._render_qweb_pdf(self.ids)
        self.l10n_py_kude_pdf = base64.b64encode(pdf_content)
        self.l10n_py_kude_filename = f"KUDE_{self.l10n_py_cdc}.pdf"

    # ============== CRON METHODS ==============

    @api.model
    def _cron_check_edi_status(self):
        """Verificar estado de documentos enviados y procesar cola de contingencia.

        Prioriza documentos cercanos al plazo de 72h.
        """
        # 1. Procesar cola de contingencia (to_send pendientes)
        contingency_docs = self.search(
            [
                ("l10n_py_edi_status", "=", "to_send"),
                ("l10n_py_emission_type", "=", "2"),
            ],
            order="l10n_py_transmission_deadline asc",
        )
        for doc in contingency_docs:
            try:
                doc.action_send_edi()
            except Exception:
                _logger.warning("Error reenviando doc contingencia %s", doc.name)

        # 2. Verificar estado de documentos ya enviados
        pending_docs = self.search(
            [
                ("l10n_py_edi_status", "in", ["sent", "processing"]),
                ("l10n_py_edi_batch_id", "!=", False),
            ]
        )

        provider = (
            self.env["ir.config_parameter"].sudo().get_param("l10n_py.edi_provider")
        )

        connector = False
        if provider == "factpy":
            connector = (
                self.env["l10n_py.edi.connector.factpy"].sudo().search([], limit=1)
            )
        elif provider == "facturasend":
            connector = (
                self.env["l10n_py.edi.connector.facturasend"].sudo().search([], limit=1)
            )

        if not connector:
            return

        for doc in pending_docs:
            try:
                response = connector.check_status(doc.l10n_py_edi_batch_id)
                if response.get("success"):
                    # Actualizar estado según respuesta
                    pass
            except Exception as e:
                _logger.error(
                    "Error verificando estado EDI para %s: %s",
                    doc.name,
                    str(e),
                )
