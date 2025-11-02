# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re


class ResPartner(models.Model):
    """
    Extensión del modelo res.partner para Paraguay
    Agrega campo RUC (Registro Único de Contribuyentes)
    """
    _inherit = 'res.partner'

    ruc = fields.Char(
        string='RUC',
        size=20,
        help='Registro Único de Contribuyentes del Paraguay',
        copy=False,
    )

    ruc_dv = fields.Char(
        string='Dígito Verificador',
        size=1,
        compute='_compute_ruc_dv',
        store=True,
        help='Dígito verificador del RUC'
    )

    taxpayer_type = fields.Selection([
        ('natural', 'Persona Física'),
        ('juridica', 'Persona Jurídica'),
        ('foreign', 'Extranjero'),
    ], string='Tipo de Contribuyente', help='Tipo de contribuyente según la SET')

    @api.depends('ruc')
    def _compute_ruc_dv(self):
        """Calcula el dígito verificador del RUC"""
        for record in self:
            if record.ruc:
                # Extraer el dígito verificador (último caracter)
                ruc_clean = record.ruc.replace('-', '').replace('.', '')
                if len(ruc_clean) > 0:
                    record.ruc_dv = ruc_clean[-1]
                else:
                    record.ruc_dv = ''
            else:
                record.ruc_dv = ''

    @api.constrains('ruc')
    def _check_ruc(self):
        """Valida el formato del RUC paraguayo"""
        for record in self:
            if record.ruc:
                # Eliminar caracteres especiales
                ruc_clean = record.ruc.replace('-', '').replace('.', '').replace(' ', '')

                # Validar que contenga solo dígitos
                if not ruc_clean.isdigit():
                    raise ValidationError(
                        _('El RUC debe contener solo números.')
                    )

                # Validar longitud (RUC paraguayo tiene entre 6 y 8 dígitos + DV)
                if len(ruc_clean) < 7 or len(ruc_clean) > 9:
                    raise ValidationError(
                        _('El RUC debe tener entre 7 y 9 dígitos (incluyendo el dígito verificador).')
                    )

                # Validar que no exista otro partner con el mismo RUC
                if record.ruc:
                    duplicate = self.search([
                        ('ruc', '=', record.ruc),
                        ('id', '!=', record.id),
                    ], limit=1)
                    if duplicate:
                        raise ValidationError(
                            _('Ya existe un contacto con el RUC %s: %s') %
                            (record.ruc, duplicate.name)
                        )

    def _format_ruc(self, ruc):
        """
        Formatea el RUC en el formato estándar: XXXXXXX-X
        """
        if not ruc:
            return ''

        # Limpiar el RUC
        ruc_clean = ruc.replace('-', '').replace('.', '').replace(' ', '')

        # Formatear: XXXXXXX-X
        if len(ruc_clean) >= 7:
            return f"{ruc_clean[:-1]}-{ruc_clean[-1]}"

        return ruc_clean

    @api.onchange('ruc')
    def _onchange_ruc(self):
        """Formatea automáticamente el RUC al ingresarlo"""
        if self.ruc:
            self.ruc = self._format_ruc(self.ruc)

    def name_get(self):
        """Muestra el nombre del partner con el RUC si está disponible"""
        result = []
        for record in self:
            name = record.name or ''
            if record.ruc and not record.is_company:
                name = f"{name} (RUC: {record.ruc})"
            elif record.ruc and record.is_company:
                name = f"{name} - RUC: {record.ruc}"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        """Permite buscar partners por RUC"""
        domain = domain or []
        if name:
            # Buscar por nombre o RUC
            domain = ['|', ('name', operator, name), ('ruc', operator, name)]
        return self._search(domain, limit=limit, order=order)
