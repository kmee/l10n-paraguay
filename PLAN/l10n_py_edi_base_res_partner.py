# l10n_py_edi_base/models/res_partner.py

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # ============== CAMPOS RUC ==============

    l10n_py_ruc = fields.Char(
        string="RUC",
        size=8,
        help="Registro Único del Contribuyente sin dígito verificador",
    )

    l10n_py_dv = fields.Char(
        string="DV",
        size=1,
        compute="_compute_dv",
        store=True,
        help="Dígito Verificador del RUC",
    )

    l10n_py_ruc_full = fields.Char(
        string="RUC Completo",
        compute="_compute_ruc_full",
        store=True,
        help="RUC con dígito verificador",
    )

    # ============== CAMPOS DE IDENTIFICACIÓN ==============

    l10n_py_taxpayer_type = fields.Selection(
        [("1", "Contribuyente"), ("2", "No Contribuyente")],
        string="Tipo de Contribuyente",
        default="2",
    )

    l10n_py_document_type = fields.Selection(
        [
            ("1", "Cédula paraguaya"),
            ("2", "Pasaporte"),
            ("3", "Cédula extranjera"),
            ("4", "Carnet de residencia"),
            ("5", "Innominado"),
            ("9", "Otro"),
        ],
        string="Tipo de Documento",
    )

    l10n_py_document_number = fields.Char(
        string="Número de Documento",
        help="Número de documento de identidad sin puntos ni guiones",
    )

    # ============== CAMPOS DE UBICACIÓN ==============

    l10n_py_department_code = fields.Integer(
        string="Código Departamento", help="Código del departamento según SET"
    )

    l10n_py_department_name = fields.Char(
        string="Departamento", compute="_compute_location_names", store=True
    )

    l10n_py_district_code = fields.Integer(
        string="Código Distrito", help="Código del distrito según SET"
    )

    l10n_py_district_name = fields.Char(
        string="Distrito", compute="_compute_location_names", store=True
    )

    l10n_py_city_code = fields.Integer(
        string="Código Ciudad", help="Código de la ciudad según SET"
    )

    l10n_py_city_name = fields.Char(
        string="Ciudad", compute="_compute_location_names", store=True
    )

    # ============== CAMPOS ADICIONALES ==============

    l10n_py_trade_name = fields.Char(
        string="Nombre Fantasía", help="Nombre comercial o de fantasía"
    )

    l10n_py_economic_activity = fields.Char(
        string="Actividad Económica", help="Código de actividad económica principal"
    )

    street_number = fields.Char(
        string="Número de Casa", help="Número de casa o edificio"
    )

    l10n_py_is_diplomatic = fields.Boolean(
        string="Es Diplomático", help="Marcar si el cliente tiene status diplomático"
    )

    l10n_py_dncp = fields.Selection(
        [("0", "Normal"), ("1", "Estado")],
        string="DNCP",
        default="0",
        help="Dirección Nacional de Contrataciones Públicas",
    )

    # ============== COMPUTE METHODS ==============

    @api.depends("l10n_py_ruc")
    def _compute_dv(self):
        """Calcular dígito verificador del RUC"""
        for partner in self:
            if partner.l10n_py_ruc:
                partner.l10n_py_dv = self._calculate_dv(partner.l10n_py_ruc)
            else:
                partner.l10n_py_dv = False

    @api.depends("l10n_py_ruc", "l10n_py_dv")
    def _compute_ruc_full(self):
        """Calcular RUC completo con DV"""
        for partner in self:
            if partner.l10n_py_ruc and partner.l10n_py_dv:
                partner.l10n_py_ruc_full = f"{partner.l10n_py_ruc}-{partner.l10n_py_dv}"
            else:
                partner.l10n_py_ruc_full = False

    @api.depends(
        "l10n_py_department_code", "l10n_py_district_code", "l10n_py_city_code"
    )
    def _compute_location_names(self):
        """Obtener nombres de ubicaciones desde los códigos"""
        for partner in self:
            # TODO: Implementar búsqueda en tablas de departamentos, distritos y ciudades
            # Por ahora, usar los valores de los campos city, state_id
            partner.l10n_py_department_name = (
                partner.state_id.name if partner.state_id else ""
            )
            partner.l10n_py_district_name = ""
            partner.l10n_py_city_name = partner.city or ""

    # ============== PRIVATE METHODS ==============

    @staticmethod
    def _calculate_dv(ruc):
        """
        Calcular dígito verificador del RUC paraguayo
        Algoritmo Módulo 11
        """
        if not ruc or not ruc.isdigit():
            return False

        # Asegurar que el RUC tenga el formato correcto
        ruc = ruc.replace("-", "").strip()

        if len(ruc) < 6:
            return False

        # Algoritmo de cálculo del DV
        base_max = 11
        k = 2
        total = 0

        # Procesar de derecha a izquierda
        for digit in reversed(ruc):
            total += int(digit) * k
            k += 1
            if k > base_max:
                k = 2

        # Calcular el dígito verificador
        remainder = total % base_max

        if remainder > 1:
            dv = base_max - remainder
        else:
            dv = 0

        return str(dv)

    def _validate_ruc_format(self, ruc):
        """Validar formato del RUC"""
        if not ruc:
            return True

        # Eliminar guiones y espacios
        ruc_clean = ruc.replace("-", "").replace(" ", "")

        # Debe ser numérico y tener entre 6 y 8 dígitos
        if not ruc_clean.isdigit():
            return False

        if len(ruc_clean) < 6 or len(ruc_clean) > 8:
            return False

        return True

    # ============== CONSTRAINT METHODS ==============

    @api.constrains("l10n_py_ruc")
    def _check_ruc_format(self):
        """Validar formato del RUC"""
        for partner in self:
            if partner.l10n_py_ruc and not self._validate_ruc_format(
                partner.l10n_py_ruc
            ):
                raise ValidationError(
                    _(
                        "El RUC debe contener entre 6 y 8 dígitos numéricos. "
                        "Formato inválido: %s"
                    )
                    % partner.l10n_py_ruc
                )

    @api.constrains("l10n_py_document_type", "l10n_py_document_number")
    def _check_document_number(self):
        """Validar número de documento según tipo"""
        for partner in self:
            if partner.l10n_py_document_type == "1" and partner.l10n_py_document_number:
                # Cédula paraguaya - validar formato
                cedula = partner.l10n_py_document_number.replace(".", "").replace(
                    ",", ""
                )
                if not cedula.isdigit():
                    raise ValidationError(
                        _("La cédula paraguaya debe contener solo números")
                    )

    @api.constrains("l10n_py_taxpayer_type", "l10n_py_ruc")
    def _check_taxpayer_requirements(self):
        """Validar requisitos según tipo de contribuyente"""
        for partner in self:
            if partner.l10n_py_taxpayer_type == "1" and not partner.l10n_py_ruc:
                raise ValidationError(
                    _("Los contribuyentes deben tener RUC obligatoriamente")
                )

    # ============== ONCHANGE METHODS ==============

    @api.onchange("l10n_py_ruc")
    def _onchange_ruc(self):
        """Validar RUC al cambiar"""
        if self.l10n_py_ruc:
            # Limpiar formato
            self.l10n_py_ruc = (
                self.l10n_py_ruc.replace("-", "").replace(" ", "").strip()
            )

            # Si es RUC válido, marcar como contribuyente
            if self._validate_ruc_format(self.l10n_py_ruc):
                self.l10n_py_taxpayer_type = "1"

    @api.onchange("country_id")
    def _onchange_country_id(self):
        """Ajustar campos según país"""
        if self.country_id and self.country_id.code != "PY":
            # Cliente extranjero
            self.l10n_py_document_type = "2"  # Pasaporte por defecto
            self.l10n_py_taxpayer_type = "2"  # No contribuyente
        else:
            # Cliente paraguayo
            if self.is_company:
                self.l10n_py_document_type = False
                self.l10n_py_taxpayer_type = "1"  # Contribuyente
            else:
                self.l10n_py_document_type = "1"  # Cédula paraguaya

    @api.onchange("is_company")
    def _onchange_is_company_py(self):
        """Ajustar tipo de contribuyente según tipo de persona"""
        if self.is_company:
            self.l10n_py_taxpayer_type = "1"  # Las empresas son contribuyentes
        else:
            # Personas físicas pueden ser o no contribuyentes
            if not self.l10n_py_taxpayer_type:
                self.l10n_py_taxpayer_type = "2"

    # ============== PUBLIC METHODS ==============

    def validate_fiscal_data(self):
        """Validar todos los datos fiscales del partner"""
        self.ensure_one()

        errors = []

        # Validar RUC si es contribuyente
        if self.l10n_py_taxpayer_type == "1":
            if not self.l10n_py_ruc:
                errors.append(_("RUC es obligatorio para contribuyentes"))
            else:
                # Validar DV
                calculated_dv = self._calculate_dv(self.l10n_py_ruc)
                if calculated_dv != self.l10n_py_dv:
                    errors.append(
                        _(
                            "El dígito verificador del RUC es incorrecto. "
                            "Debería ser: %s"
                        )
                        % calculated_dv
                    )

        # Validar documento
        if not self.l10n_py_document_type and not self.is_company:
            errors.append(_("Tipo de documento es obligatorio para personas físicas"))

        if self.l10n_py_document_type and not self.l10n_py_document_number:
            errors.append(_("Número de documento es obligatorio"))

        # Validar dirección para facturación electrónica
        if not self.street:
            errors.append(_("La dirección es obligatoria para facturación electrónica"))

        # Validar ubicación
        if self.country_id and self.country_id.code == "PY":
            if not self.l10n_py_department_code:
                errors.append(
                    _("El departamento es obligatorio para clientes paraguayos")
                )

        if errors:
            raise ValidationError("\n".join(errors))

        return True

    @api.model
    def create_from_ruc(self, ruc):
        """
        Crear partner desde RUC consultando servicio externo
        TODO: Implementar consulta a servicio de SET o proveedor
        """
        # Validar formato
        if not self._validate_ruc_format(ruc):
            raise ValidationError(_("Formato de RUC inválido"))

        # Calcular DV
        ruc_clean = ruc.replace("-", "").strip()
        dv = self._calculate_dv(ruc_clean)

        # TODO: Consultar datos del RUC en servicio externo
        # Por ahora, crear con datos mínimos

        partner = self.create(
            {
                "name": f"Cliente RUC {ruc_clean}-{dv}",
                "l10n_py_ruc": ruc_clean,
                "l10n_py_taxpayer_type": "1",
                "is_company": True,
                "country_id": self.env.ref("base.py").id,
            }
        )

        return partner

    def action_validate_with_set(self):
        """
        Validar RUC con el servicio de SET
        TODO: Implementar cuando esté disponible el servicio
        """
        self.ensure_one()

        if not self.l10n_py_ruc:
            raise ValidationError(_("No hay RUC para validar"))

        # TODO: Implementar consulta a SET

        # Por ahora, solo validar formato y DV
        self.validate_fiscal_data()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Validación Exitosa"),
                "message": _("Los datos fiscales son válidos"),
                "type": "success",
                "sticky": False,
            },
        }
