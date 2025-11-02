# l10n_py_edi_base/models/account_move.py

import logging
import random
import string

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    # ============== CAMPOS EDI PARAGUAY ==============

    l10n_py_edi_document_type = fields.Selection(
        [
            ("1", "Factura Electrónica"),
            ("4", "Autofactura Electrónica"),
            ("5", "Nota de Crédito Electrónica"),
            ("6", "Nota de Débito Electrónica"),
            ("7", "Nota de Remisión Electrónica"),
        ],
        string="Tipo Documento Electrónico",
        compute="_compute_edi_document_type",
        store=True,
    )

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

    # ============== COMPUTE METHODS ==============

    @api.depends("move_type", "debit_origin_id")
    def _compute_edi_document_type(self):
        for move in self:
            if move.move_type == "out_invoice":
                move.l10n_py_edi_document_type = "1"  # Factura
            elif move.move_type == "out_refund":
                move.l10n_py_edi_document_type = "5"  # Nota de Crédito
            elif (
                move.move_type == "in_invoice"
                and move.partner_id.id == move.company_id.partner_id.id
            ):
                move.l10n_py_edi_document_type = "4"  # Autofactura
            elif move.debit_origin_id:
                move.l10n_py_edi_document_type = "6"  # Nota de Débito
            else:
                move.l10n_py_edi_document_type = False

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
                    _("El código de seguridad debe tener exactamente 9 caracteres")
                )

    # ============== PRIVATE METHODS ==============

    def _generate_security_code(self):
        """Generar código de seguridad aleatorio de 9 dígitos"""
        return "".join(random.choices(string.digits, k=9))

    def _prepare_edi_document_data(self):
        """Preparar datos del documento electrónico en formato JSON"""
        self.ensure_one()

        if not self.l10n_py_security_code:
            self.l10n_py_security_code = self._generate_security_code()

        # Construir estructura de datos según formato requerido
        document_data = {
            "tipoDocumento": int(self.l10n_py_edi_document_type),
            "establecimiento": self.journal_id.l10n_py_establishment or "001",
            "punto": self.journal_id.l10n_py_point or "001",
            "numero": self._get_edi_sequence_number(),
            "descripcion": self.name or "",
            "observacion": self.narration or "",
            "fecha": self.invoice_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "tipoEmision": int(self.l10n_py_emission_type),
            "tipoTransaccion": int(self.l10n_py_transaction_type),
            "tipoImpuesto": 1,  # IVA
            "moneda": self.currency_id.name,
            "receiptId": self.l10n_py_receipt_id or f"{self.company_id.id}-{self.id}",
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

        return document_data

    def _prepare_customer_data(self):
        """Preparar datos del cliente"""
        partner = self.partner_id

        customer_data = {
            "contribuyente": partner.l10n_py_taxpayer_type == "1",
            "ruc": partner.l10n_py_ruc or "",
            "razonSocial": partner.name,
            "nombreFantasia": partner.trade_name or partner.name,
            "tipoOperacion": 1,  # B2B
            "direccion": partner.street or "N/A",
            "numeroCasa": partner.street_number or "0",
            "pais": partner.country_id.code or "PRY",
            "paisDescripcion": partner.country_id.name or "Paraguay",
        }

        # Agregar datos de ubicación si están disponibles
        if partner.l10n_py_department_code:
            customer_data.update(
                {
                    "departamento": partner.l10n_py_department_code,
                    "departamentoDescripcion": partner.l10n_py_department_name,
                    "distrito": partner.l10n_py_district_code or 0,
                    "distritoDescripcion": partner.l10n_py_district_name or "",
                    "ciudad": partner.l10n_py_city_code or 0,
                    "ciudadDescripcion": partner.city or "",
                }
            )

        # Agregar contacto
        if partner.phone or partner.mobile:
            customer_data["telefono"] = partner.phone or ""
            customer_data["celular"] = partner.mobile or ""

        if partner.email:
            customer_data["email"] = partner.email

        # Agregar tipo y número de documento
        if partner.l10n_py_document_type:
            customer_data["tipoContribuyente"] = 1 if partner.is_company else 2
            customer_data["documentoTipo"] = int(partner.l10n_py_document_type)
            customer_data["documentoNumero"] = (
                partner.vat or partner.l10n_py_document_number or ""
            )

        return customer_data

    def _prepare_payment_condition(self):
        """Preparar condición de pago"""
        payment_condition = {
            "tipo": 2 if self.invoice_payment_term_id else 1,  # 1: Contado, 2: Crédito
        }

        if self.invoice_payment_term_id:
            # Es crédito
            payment_condition["credito"] = {
                "tipo": 1,  # 1: Plazo, 2: Cuotas
                "plazo": f"{self.invoice_payment_term_id.line_ids[0].value} días",
                "cuotas": len(self.invoice_payment_term_id.line_ids),
            }

            # Preparar información de cuotas
            cuotas = []
            for i, line in enumerate(self.invoice_payment_term_id.line_ids):
                due_date = self.invoice_date + relativedelta(days=line.value)
                cuotas.append(
                    {
                        "moneda": self.currency_id.name,
                        "monto": self.amount_total
                        / len(self.invoice_payment_term_id.line_ids),
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

            # Calcular base gravable e IVA
            if iva_type == 1:  # Gravado
                base_grav = line.price_subtotal / (1 + iva_rate / 100)
                line.price_subtotal - base_grav
            else:
                base_grav = 0

            item = {
                "codigo": line.product_id.default_code or f"PROD-{line.product_id.id}",
                "descripcion": line.name or line.product_id.name,
                "observacion": "",
                "ncm": line.product_id.l10n_py_ncm_code or "",
                "unidadMedida": 77,  # UNI - Unidad
                "cantidad": line.quantity,
                "precioUnitario": line.price_unit,
                "cambio": 0,
                "ivaTipo": iva_type,
                "ivaBase": 100,
                "iva": iva_rate,
                "lote": line.lot_name or "",
                "vencimiento": "",
            }

            items.append(item)

        return items

    def _get_edi_sequence_number(self):
        """Obtener número de secuencia para EDI"""
        # Tomar los últimos 7 dígitos del número de factura
        if self.name:
            number = "".join(filter(str.isdigit, self.name.split("/")[-1]))
            return number.zfill(7)[-7:]
        return "0000001"

    def _validate_edi_data(self):
        """Validar datos antes de enviar a EDI"""
        errors = []

        # Validar datos de la empresa
        company = self.company_id
        if not company.l10n_py_ruc:
            errors.append(_("Configure el RUC de la empresa"))

        # Validar datos del cliente
        partner = self.partner_id
        if not partner.l10n_py_ruc and partner.l10n_py_taxpayer_type == "1":
            errors.append(_("El cliente contribuyente debe tener RUC"))

        if not partner.street:
            errors.append(_("La dirección del cliente es obligatoria"))

        # Validar datos del diario
        journal = self.journal_id
        if not journal.l10n_py_timbrado:
            errors.append(_("Configure el timbrado en el diario"))

        if (
            journal.l10n_py_timbrado_validity
            and journal.l10n_py_timbrado_validity < fields.Date.today()
        ):
            errors.append(_("El timbrado está vencido"))

        # Validar productos
        for line in self.invoice_line_ids.filtered(lambda l: not l.display_type):
            if not line.product_id.l10n_py_ncm_code:
                errors.append(
                    _("El producto %s no tiene código NCM") % line.product_id.name
                )

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
            connector = self.env["l10n_py.edi.connector.factpy"].sudo()
        elif provider == "facturasend":
            connector = self.env["l10n_py.edi.connector.facturasend"].sudo()
        else:
            raise UserError(_("No hay un proveedor EDI configurado"))

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
            _logger.error(f"Error enviando EDI: {str(e)}")
            self.l10n_py_edi_status = "error"
            self.l10n_py_edi_message = str(e)
            raise UserError(_("Error enviando documento: %s") % str(e))

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
                    "l10n_py_edi_message": "Documento aceptado exitosamente",
                }
            )

            # Guardar XML si viene
            if de_data.get("xml"):
                self.l10n_py_edi_xml = de_data["xml"].encode("utf-8")
                self.l10n_py_edi_xml_filename = f"{self.l10n_py_cdc}.xml"

            # TODO: Generar QR code como imagen
            # TODO: Solicitar/generar KUDE

    def action_cancel_edi(self):
        """Cancelar documento electrónico"""
        self.ensure_one()

        if not self.l10n_py_cdc:
            raise UserError(_("No se puede cancelar un documento sin CDC"))

        # TODO: Implementar cancelación con el proveedor EDI

        self.l10n_py_edi_status = "cancelled"
        self.l10n_py_edi_message = f"Cancelado el {fields.Datetime.now()}"

    def action_retry_edi(self):
        """Reintentar envío de documento"""
        self.ensure_one()

        if self.l10n_py_edi_status not in ["error", "rejected"]:
            raise UserError(
                _("Solo se pueden reintentar documentos con error o rechazados")
            )

        return self.action_send_edi()

    def action_download_xml(self):
        """Descargar XML del documento"""
        self.ensure_one()

        if not self.l10n_py_edi_xml:
            raise UserError(_("No hay XML disponible para este documento"))

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{self._name}/{self.id}/l10n_py_edi_xml/{self.l10n_py_edi_xml_filename}?download=true",
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
            "url": f"/web/content/{self._name}/{self.id}/l10n_py_kude_pdf/{self.l10n_py_kude_filename}?download=true",
            "target": "self",
        }

    def _generate_kude(self):
        """Generar KUDE (representación impresa)"""
        # TODO: Implementar generación de KUDE

    # ============== CRON METHODS ==============

    @api.model
    def _cron_check_edi_status(self):
        """Verificar estado de documentos enviados"""
        pending_docs = self.search(
            [
                ("l10n_py_edi_status", "in", ["sent", "processing"]),
                ("l10n_py_edi_batch_id", "!=", False),
            ]
        )

        for doc in pending_docs:
            try:
                # TODO: Consultar estado con el proveedor
                pass
            except Exception as e:
                _logger.error(f"Error verificando estado EDI para {doc.name}: {str(e)}")
