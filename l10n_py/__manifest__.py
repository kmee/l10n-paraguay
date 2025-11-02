# -*- coding: utf-8 -*-
{
    'name': 'Paraguay - Accounting',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Localizations/Account Charts',
    'summary': 'Localización contable para Paraguay',
    'description': """
Localización Paraguaya - Contabilidad
======================================

Este módulo incluye:
--------------------
    * Plan de cuentas estándar para Paraguay
    * Configuración de impuestos (IVA 10%, IVA 5%, Exento)
    * Gestión de timbrados (autorizaciones de facturación)
    * Campos específicos para facturas paraguayas
    * Validación de RUC (Registro Único de Contribuyentes)
    * Cálculo automático de IVA discriminado
    * Reportes de facturas según normativa paraguaya

Características principales:
----------------------------
    * Control de timbrados con fechas de vigencia
    * Numeración autorizada de facturas
    * Discriminación automática de IVA 5%, 10% y exento
    * Campo RUC en clientes y proveedores
    * Conversión de montos a letras (guaraníes)
    """,
    'author': 'KMEE',
    'website': 'https://github.com/kmee',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'base',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/account_tax_group_data.xml',
        'data/account_chart_template_data.xml',

        # Views
        'views/account_authorization_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
    ],
    'demo': [
        'demo/account_authorization_demo.xml',
        'demo/res_partner_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
