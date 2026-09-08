# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    itau_enabled = fields.Boolean(
        string="Banco Itaú (Open Banking)",
        help="Habilita la integración con el canal Itaú Open Banking "
        "(IOB) para esta cuenta bancaria: autenticación mTLS compartida "
        "por las APIs de Business Account, Account Statements, Payments "
        "Platform y Transfer Information.",
    )
    itau_environment = fields.Selection(
        [("testing", "Testing"), ("production", "Producción")],
        string="Entorno Itaú",
        default="testing",
    )
    itau_production_url = fields.Char(
        string="URL de Entorno Itaú",
        help="El banco no publica una URL de testing/sandbox de forma "
        "pública (a diferencia de Banco Atlas) -- solicitar al banco y "
        "completar aquí, tanto para Testing como para Producción.",
    )
    itau_ruc_empresa = fields.Char(
        string="RUC de la Empresa (Itaú)",
        help="RUC usado para autenticarse en el portal '24 Horas "
        "Negocios' y, previsiblemente, como identificador en las "
        "llamadas a la API (a confirmar en Fase 3 contra la "
        "documentación real del banco).",
    )
    itau_codigo_empresa = fields.Char(
        string="Código de Empresa (Itaú)",
        help="Código de empresa asignado por el Banco Itaú, visible en "
        "el portal '24 Horas Negocios'.",
    )
    itau_client_cert = fields.Binary(
        string="Certificado mTLS (PEM)",
        groups="account.group_account_manager",
        help="Certificado de cliente (PEM) emitido para el servidor que "
        "realizará las llamadas -- solicitado durante la suscripción "
        "digital al canal ('Solicitar certificado mTLS').",
    )
    itau_client_cert_filename = fields.Char(string="Nombre del Archivo (Certificado)")
    itau_client_key = fields.Binary(
        string="Clave Privada mTLS (PEM)",
        groups="account.group_account_manager",
        help="Clave privada (PEM) correspondiente al certificado mTLS. "
        "Nunca se persiste en disco de forma permanente: el cliente "
        "HTTP la materializa en un archivo temporal solo durante la "
        "duración de cada llamada y lo elimina inmediatamente después "
        "(ver ItauApiClient._write_temp_cert_pair).",
    )
    itau_client_key_filename = fields.Char(string="Nombre del Archivo (Clave)")
    itau_canal_token = fields.Char(
        string="Token de Canal Itaú",
        groups="account.group_account_manager",
        help="Placeholder: la presentación comercial del banco menciona "
        "un 'token de canal para validar cada operación' como capa de "
        "seguridad adicional a mTLS, IP whitelisting e iToken, pero no "
        "detalla cómo se obtiene ni en qué header se envía. Sin uso "
        "confirmado hasta la Fase 3 de este trabajo.",
    )
