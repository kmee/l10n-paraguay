# Copyright 2026 KMEE
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Override de account.chart.template para inyectar datos demo paraguayos.

Sigue el mismo patrón del core (``addons/account/demo/account_demo.py``):
``_get_demo_data`` es un *generator* que yielda tuplas ``(model, dict)``;
``_create_demo_data`` itera y persiste vía ``_load_records``;
``_post_create_demo_data`` hace ``action_post`` automáticamente para
``account.move``. Aquí extendemos ``_post_create_demo_data`` para,
luego de postear, llamar a ``action_preview_xml`` y distribuir estados
EDI realistas (accepted / sent / rejected / draft).
"""
import logging
import random
import time
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import Command, _, api, fields, models

_logger = logging.getLogger(__name__)


# Distribución de estados EDI para las facturas demo (suma 100)
_EDI_STATE_DISTRIBUTION = [
    ("accepted", 70),
    ("sent", 15),
    ("rejected", 10),
    ("draft", 5),
]


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    # ------------------------------------------------------------------ #
    # Override del generator principal                                   #
    # ------------------------------------------------------------------ #

    @api.model
    def _get_demo_data(self):
        py_template = self.env.ref(
            "l10n_py.py_chart_template", raise_if_not_found=False
        )
        if py_template and self == py_template:
            # Solo emite datos PY si ``l10n_py_account`` ya cargó sus
            # demo XMLs (partners/products). Durante el primer ``try_loading``
            # —disparado por ``l10n_py``— el módulo aún no existe en el
            # sistema; verificamos vía un xmlid clave de los demo files.
            anchor = self.env.ref(
                "l10n_py_account.partner_contribuyente_general",
                raise_if_not_found=False,
            )
            if not anchor:
                return
            yield self._get_demo_data_l10n_py_invoices()
            yield self._get_demo_data_l10n_py_operating_expenses()
            yield self._get_demo_data_l10n_py_payroll()
            yield self._get_demo_data_l10n_py_depreciation()
            yield self._get_demo_data_l10n_py_forecast()
            return
        # Otros templates: pasa al core sin modificación
        yield from super()._get_demo_data()

    # ------------------------------------------------------------------ #
    # Generators específicos                                             #
    # ------------------------------------------------------------------ #

    def _l10n_py_demo_months(self):
        """Devuelve lista de (offset_meses, date_iso) desde hace 11 meses
        hasta el mes actual (12 meses en total — cubre todas las columnas
        del informe ``Estado de Resultados (Mensual)``)."""
        today = fields.Date.today()
        return [
            (m, (today - relativedelta(months=m)).replace(day=10).isoformat())
            for m in range(11, -1, -1)
        ]

    @api.model
    def _get_demo_data_l10n_py_invoices(self):
        """Facturas cliente y proveedor distribuidas en 6 meses retroactivos."""
        cid = self.env.company.id
        ref = self.env.ref
        data = {}

        client_partners = [
            "l10n_py_account.partner_contribuyente_general",
            "l10n_py_account.partner_contribuyente_servicios",
            "l10n_py_account.partner_no_contribuyente_ci",
            "l10n_py_account.partner_extranjero",
        ]
        supplier_partner = "l10n_py_account.partner_proveedor_py"

        products_iva10 = [
            "l10n_py_account.product_iva_10_electronica",
            "l10n_py_account.product_iva_10_servicio",
        ]
        products_iva5 = [
            "l10n_py_account.product_iva_5_alimento",
            "l10n_py_account.product_iva_5_farmacia",
        ]
        products_exento = [
            "l10n_py_account.product_exento_libro",
        ]

        timbrado = ref(
            "l10n_py_account.demo_authorization_001", raise_if_not_found=False
        )
        doc_type_fe = ref(
            "l10n_py_account.dc_py_f", raise_if_not_found=False
        )

        pt_immediate = ref(
            "account.account_payment_term_immediate",
            raise_if_not_found=False,
        )
        pt_30days = ref(
            "account.account_payment_term_30days", raise_if_not_found=False
        )

        for month_off, date_iso in self._l10n_py_demo_months():
            # 3 facturas cliente por mes
            for n, partner_xmlid in enumerate(client_partners[:3]):
                lines = []
                # mezcla de líneas IVA 10 / IVA 5 / exento
                lines.append(
                    Command.create(
                        {
                            "product_id": ref(products_iva10[n % 2]).id,
                            "quantity": 1 + n,
                            "price_unit": 1500000 + n * 250000,
                        }
                    )
                )
                if n % 2 == 0:
                    lines.append(
                        Command.create(
                            {
                                "product_id": ref(products_iva5[n % 2]).id,
                                "quantity": 10 + n * 5,
                                "price_unit": 45000,
                            }
                        )
                    )
                if n == 0:
                    lines.append(
                        Command.create(
                            {
                                "product_id": ref(products_exento[0]).id,
                                "quantity": 3,
                                "price_unit": 80000,
                            }
                        )
                    )
                vals = {
                    "move_type": "out_invoice",
                    "partner_id": ref(partner_xmlid).id,
                    "invoice_date": date_iso,
                    "invoice_line_ids": lines,
                }
                # n=1 → à crédito 30 días; n=0,2 → a vista (contado)
                if n == 1 and pt_30days:
                    vals["invoice_payment_term_id"] = pt_30days.id
                elif pt_immediate:
                    vals["invoice_payment_term_id"] = pt_immediate.id
                if timbrado:
                    vals["l10n_py_authorization_id"] = timbrado.id
                if doc_type_fe:
                    vals["l10n_latam_document_type_id"] = doc_type_fe.id
                data[f"{cid}_demo_py_inv_m{month_off}_{n}"] = vals

            # 2 facturas proveedor por mes. En PY el ``name`` de la in_invoice
            # es el número del documento del proveedor (manual), no viene de
            # secuencia. Lo seteamos igual al ``ref`` para satisfacer la
            # validación LATAM (journal con documentos requiere doc_type +
            # número).
            for n in range(2):
                ref_doc = f"FE 001-001-{(month_off + 1) * 100 + n:07d}"
                vals = {
                    "move_type": "in_invoice",
                    "partner_id": ref(supplier_partner).id,
                    "invoice_date": date_iso,
                    "ref": ref_doc,
                    "name": ref_doc,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "product_id": ref(
                                    products_iva10[n % 2]
                                ).id,
                                "quantity": 5 + n * 2,
                                "price_unit": 950000,
                            }
                        )
                    ],
                }
                if doc_type_fe:
                    vals["l10n_latam_document_type_id"] = doc_type_fe.id
                data[f"{cid}_demo_py_bill_m{month_off}_{n}"] = vals

        return ("account.move", data)

    @api.model
    def _get_demo_data_l10n_py_operating_expenses(self):
        """Asientos manuales mensuales de gastos comerciales y administrativos."""
        cid = self.env.company.id
        company = self.env.company
        Account = self.env["account.account"]

        def acc(code):
            return Account.search(
                [
                    ("code", "=like", f"{code}%"),
                    ("company_id", "=", company.id),
                ],
                limit=1,
                order="code",
            )

        # Cuentas de gastos
        a_alquileres = acc("11.05")
        a_combustibles = acc("11.08")
        a_publicidad = acc("10.04")
        a_comisiones = acc("10.02")
        a_intereses_bcos = acc("13.01")
        a_caja = acc("1.01.01.02")
        a_bancos = acc("1.01.01.04")

        data = {}
        if not (a_alquileres and a_caja):
            _logger.warning(
                "l10n_py demo: no se encontraron cuentas para gastos operativos"
            )
            return ("account.move", data)

        for month_off, date_iso in self._l10n_py_demo_months():
            # Asiento mensual de gastos diversos
            lines = []
            if a_alquileres:
                lines.append(
                    Command.create(
                        {
                            "account_id": a_alquileres.id,
                            "name": "Alquileres mensuales",
                            "debit": 3500000,
                            "credit": 0,
                        }
                    )
                )
            if a_combustibles:
                lines.append(
                    Command.create(
                        {
                            "account_id": a_combustibles.id,
                            "name": "Combustibles y energía",
                            "debit": 1200000,
                            "credit": 0,
                        }
                    )
                )
            if a_publicidad:
                lines.append(
                    Command.create(
                        {
                            "account_id": a_publicidad.id,
                            "name": "Publicidad y propaganda",
                            "debit": 800000,
                            "credit": 0,
                        }
                    )
                )
            if a_comisiones:
                lines.append(
                    Command.create(
                        {
                            "account_id": a_comisiones.id,
                            "name": "Comisiones pagadas",
                            "debit": 650000,
                            "credit": 0,
                        }
                    )
                )
            if a_intereses_bcos:
                lines.append(
                    Command.create(
                        {
                            "account_id": a_intereses_bcos.id,
                            "name": "Intereses bancarios",
                            "debit": 420000,
                            "credit": 0,
                        }
                    )
                )
            total_debit = sum(
                line[2].get("debit", 0) for line in lines
            )
            # Crédito en banco
            lines.append(
                Command.create(
                    {
                        "account_id": (a_bancos or a_caja).id,
                        "name": "Pagos del mes",
                        "debit": 0,
                        "credit": total_debit,
                    }
                )
            )
            data[f"{cid}_demo_py_opex_m{month_off}"] = {
                "move_type": "entry",
                "date": date_iso,
                "ref": f"Gastos operativos {date_iso[:7]}",
                "line_ids": lines,
            }
        return ("account.move", data)

    @api.model
    def _get_demo_data_l10n_py_payroll(self):
        """Asiento manual mensual de remuneraciones."""
        cid = self.env.company.id
        company = self.env.company
        Account = self.env["account.account"]

        def acc(code):
            return Account.search(
                [
                    ("code", "=like", f"{code}%"),
                    ("company_id", "=", company.id),
                ],
                limit=1,
                order="code",
            )

        a_sueldos_com = acc("10.01.01")  # Comerciales
        a_aportes_com = acc("10.01.02")
        a_sueldos_adm = acc("11.01.01")  # Administrativos
        a_aportes_adm = acc("11.01.02")
        a_remun_pagar = acc("2.01.03")  # Remuneraciones a pagar

        data = {}
        if not (a_sueldos_com and a_remun_pagar):
            return ("account.move", data)

        for month_off, date_iso in self._l10n_py_demo_months():
            lines = [
                Command.create(
                    {
                        "account_id": a_sueldos_com.id,
                        "name": "Sueldos comerciales",
                        "debit": 12500000,
                        "credit": 0,
                    }
                ),
                Command.create(
                    {
                        "account_id": a_aportes_com.id,
                        "name": "Aporte patronal comerciales",
                        "debit": 2125000,
                        "credit": 0,
                    }
                )
                if a_aportes_com
                else None,
                Command.create(
                    {
                        "account_id": a_sueldos_adm.id,
                        "name": "Sueldos administrativos",
                        "debit": 18000000,
                        "credit": 0,
                    }
                )
                if a_sueldos_adm
                else None,
                Command.create(
                    {
                        "account_id": a_aportes_adm.id,
                        "name": "Aporte patronal administrativos",
                        "debit": 3060000,
                        "credit": 0,
                    }
                )
                if a_aportes_adm
                else None,
            ]
            lines = [line for line in lines if line is not None]
            total_debit = sum(line[2]["debit"] for line in lines)
            lines.append(
                Command.create(
                    {
                        "account_id": a_remun_pagar.id,
                        "name": "Remuneraciones a pagar",
                        "debit": 0,
                        "credit": total_debit,
                    }
                )
            )
            data[f"{cid}_demo_py_payroll_m{month_off}"] = {
                "move_type": "entry",
                "date": date_iso,
                "ref": f"Nómina {date_iso[:7]}",
                "line_ids": lines,
            }
        return ("account.move", data)

    @api.model
    def _get_demo_data_l10n_py_depreciation(self):
        """Depreciación mensual de bienes de uso."""
        cid = self.env.company.id
        company = self.env.company
        Account = self.env["account.account"]

        def acc(code):
            return Account.search(
                [
                    ("code", "=like", f"{code}%"),
                    ("company_id", "=", company.id),
                ],
                limit=1,
                order="code",
            )

        a_dep_gasto = acc("15.01")          # Depreciaciones del ejercicio
        a_dep_acum = acc("1.02.04.99")      # Depreciación acumulada (Bienes de Uso)

        data = {}
        if not (a_dep_gasto and a_dep_acum):
            return ("account.move", data)

        for month_off, date_iso in self._l10n_py_demo_months():
            data[f"{cid}_demo_py_depreciation_m{month_off}"] = {
                "move_type": "entry",
                "date": date_iso,
                "ref": f"Depreciación mensual {date_iso[:7]}",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": a_dep_gasto.id,
                            "name": "Depreciación de bienes de uso",
                            "debit": 4200000,
                            "credit": 0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": a_dep_acum.id,
                            "name": "Depreciación acumulada",
                            "debit": 0,
                            "credit": 4200000,
                        }
                    ),
                ],
            }
        return ("account.move", data)

    @api.model
    def _get_demo_data_l10n_py_forecast(self):
        """Forecast lines para las próximas 12 semanas — alimenta el DFC forecast."""
        if "mis.cash_flow.forecast_line" not in self.env:
            return ("mis.cash_flow.forecast_line", {})

        cid = self.env.company.id
        company = self.env.company
        Account = self.env["account.account"]
        today = fields.Date.today()

        def acc(code):
            return Account.search(
                [
                    ("code", "=like", f"{code}%"),
                    ("company_id", "=", company.id),
                ],
                limit=1,
                order="code",
            )

        a_bancos = acc("1.01.01.04")
        if not a_bancos:
            return ("mis.cash_flow.forecast_line", {})

        # 12 entradas y 8 salidas distribuidas en las próximas 12 semanas
        data = {}
        scenarios = [
            (+1, "Cobranza factura cliente prevista", 8500000),
            (+2, "Cobranza cliente proyecto refrigeración", 12500000),
            (-2, "Pago proveedor importación", -7200000),
            (+3, "Anticipo cliente exportación", 18000000),
            (-3, "Pago nómina quincenal", -16800000),
            (+4, "Cobranza saldo abierto", 6500000),
            (-5, "Pago alquileres trimestral", -10500000),
            (+6, "Cobranza factura mayorista", 22000000),
            (-7, "Pago IVA mensual", -3850000),
            (+8, "Cobranza cliente recurrente", 4500000),
            (-9, "Pago comisiones vendedores", -2750000),
            (+10, "Anticipo cliente nuevo proyecto", 15500000),
            (-11, "Pago intereses préstamo", -1850000),
            (+12, "Cobranza exportación FOB", 28000000),
        ]
        for i, (weeks, name, balance) in enumerate(scenarios):
            data[f"{cid}_demo_py_forecast_{i:02d}"] = {
                "date": (today + timedelta(weeks=weeks)).isoformat(),
                "name": name,
                "balance": balance,
                "account_id": a_bancos.id,
                "company_id": company.id,
            }
        return ("mis.cash_flow.forecast_line", data)

    # ------------------------------------------------------------------ #
    # Post-creación: postear + previsualizar XML + estados EDI           #
    # ------------------------------------------------------------------ #

    @api.model
    def _post_create_demo_data(self, created):
        py_template = self.env.ref(
            "l10n_py.py_chart_template", raise_if_not_found=False
        )
        is_py = bool(py_template and self == py_template)

        # Si NO somos el template PY: comportamiento default
        if not is_py:
            super()._post_create_demo_data(created)
            return

        # Somos PY: el super del core (``account_demo._post_create_demo_data``)
        # asume xmlids ``{cid}_demo_invoice_extract`` que solo existen cuando se
        # consumen los generators del core. Como omitimos esos generators,
        # postamos manualmente las facturas y nos saltamos el super.
        if created._name == "account.move":
            for move in created:
                try:
                    move._post(soft=False)
                except Exception as e:  # noqa: BLE001
                    _logger.warning(
                        "l10n_py demo: no se pudo postear %s: %s",
                        move.name or move.id,
                        e,
                    )
        elif created._name != "account.move":
            return

        if created._name != "account.move":
            return

        # Construye lista de estados ponderada
        weighted = []
        for state, weight in _EDI_STATE_DISTRIBUTION:
            weighted.extend([state] * weight)
        rng = random.Random(42)  # determinístico

        pt_immediate = self.env.ref(
            "account.account_payment_term_immediate",
            raise_if_not_found=False,
        )

        # Guard: la lógica EDI / preview XML solo aplica si ``l10n_py_edi_base``
        # está disponible (campo ``l10n_py_edi_status`` + método
        # ``action_preview_xml`` vienen de ahí).
        Move = self.env["account.move"]
        has_edi = "l10n_py_edi_status" in Move._fields and hasattr(
            Move, "action_preview_xml"
        )

        # Bootstrap prerequisitos para action_preview_xml:
        # - Journals de venta deben tener timbrado
        # - Productos deben tener NCM
        if has_edi:
            self._l10n_py_demo_bootstrap_journals_products()

        for move in created:
            # Solo procesa facturas de venta con timbrado
            if move.move_type != "out_invoice" or not move.l10n_py_authorization_id:
                continue
            if not has_edi:
                # Sin EDI base no podemos preview ni manipular estados
                continue
            try:
                move.action_preview_xml()
            except Exception as e:  # noqa: BLE001
                _logger.warning(
                    "l10n_py demo: action_preview_xml falló para %s: %s",
                    move.name,
                    e,
                )
                continue

            target = rng.choice(weighted)
            vals = {}
            if target != "draft":
                vals["l10n_py_edi_status"] = target
            if target == "accepted":
                vals["l10n_py_edi_message"] = (
                    "Aprobado por SIFEN (simulado — demo)"
                )
                vals["l10n_py_edi_batch_id"] = (
                    f"DEMO-{move.id:06d}"
                )
                # CDC sintético (44 dígitos) — solo si vacío
                if not move.l10n_py_cdc:
                    company = move.company_id
                    ruc = (company.l10n_py_ruc or "80000000").zfill(8)
                    dv = company.l10n_py_dv or "0"
                    auth = move.l10n_py_authorization_id
                    est = (auth.establishment or "001") if auth else "001"
                    pun = (auth.expedition_point or "001") if auth else "001"
                    seq = (move.name or "").replace("FE ", "").zfill(7)[-7:]
                    fec = (
                        move.invoice_date
                        and move.invoice_date.strftime("%Y%m%d")
                        or time.strftime("%Y%m%d")
                    )
                    sec = move.l10n_py_security_code or f"{move.id:09d}"
                    base = f"01{ruc}{dv}{est}{pun}{seq}1{fec}{sec}"
                    cdc = (base + "0" * 44)[:44]
                    vals["l10n_py_cdc"] = cdc
            elif target == "sent":
                vals["l10n_py_edi_message"] = (
                    "Enviado a SIFEN, pendiente de respuesta (simulado)"
                )
            elif target == "rejected":
                vals["l10n_py_edi_message"] = (
                    "Rechazado por SIFEN: glosa 9876 — datos del receptor "
                    "incompletos (simulado para demo)"
                )
            if vals:
                move.write(vals)

            # Registrar pago / recibo:
            # - factura "contado" (immediate): paga en invoice_date (sin recibo)
            # - factura "à crédito" (>=30d): si vencida, paga ahora y emite recibo
            # - factura à crédito reciente: queda no_paid (pendiente recibo)
            if target == "rejected":
                continue  # rechazada no se cobra
            is_credit = bool(
                move.invoice_payment_term_id
                and pt_immediate
                and move.invoice_payment_term_id.id != pt_immediate.id
            )
            try:
                self._l10n_py_register_demo_payment(move, is_credit, rng)
            except Exception as e:  # noqa: BLE001
                _logger.warning(
                    "l10n_py demo: payment para %s falló: %s", move.name, e
                )

    # ------------------------------------------------------------------ #
    # Bootstrap de prerequisitos                                         #
    # ------------------------------------------------------------------ #

    @api.model
    def _l10n_py_demo_bootstrap_journals_products(self):
        """Configura timbrado en journals de venta y NCM en productos demo.

        Estos campos son requeridos por ``account_move.action_preview_xml``
        (validación ``_validate_edi_data``). En demo no existe un wizard que
        los configure, así que lo hacemos en bootstrap."""
        Auth = self.env["account.authorization"]
        auth = self.env.ref(
            "l10n_py_account.demo_authorization_001",
            raise_if_not_found=False,
        ) or Auth.search([("company_id", "=", self.env.company.id)], limit=1)
        if auth:
            sale_journals = self.env["account.journal"].search(
                [("type", "=", "sale"), ("company_id", "=", self.env.company.id)]
            )
            for j in sale_journals:
                if (
                    "l10n_py_authorization_id" in j._fields
                    and not j.l10n_py_authorization_id
                ):
                    j.l10n_py_authorization_id = auth.id

        # NCM en productos sin código (default Mercosur: 21011200)
        Product = self.env["product.product"]
        if "l10n_py_ncm_code" in Product._fields:
            Product.search([("l10n_py_ncm_code", "=", False)]).write(
                {"l10n_py_ncm_code": "21011200"}
            )
            Template = self.env["product.template"]
            if "l10n_py_ncm_code" in Template._fields:
                Template.search([("l10n_py_ncm_code", "=", False)]).write(
                    {"l10n_py_ncm_code": "21011200"}
                )

    # ------------------------------------------------------------------ #
    # Pago / Recibo                                                      #
    # ------------------------------------------------------------------ #

    @api.model
    def _l10n_py_register_demo_payment(self, move, is_credit, rng=None):
        """Genera un pago para la factura cliente.

        - Factura *a vista* (contado): pago en ``invoice_date``. No emite
          recibo (no aplica para venta al contado en PY).
        - Factura *a crédito* vencida: pago entre invoice_date y hoy +
          emite *recibo electrónico de cobranza* (mensaje en el chatter
          del payment con la referencia ``RE-<id>``).
        - Factura *a crédito reciente* (no vencida): se queda abierta,
          pendiente de cobranza/recibo.
        """
        from datetime import timedelta

        today = fields.Date.today()
        company = move.company_id
        Journal = self.env["account.journal"]
        bank = Journal.search(
            [("type", "=", "bank"), ("company_id", "=", company.id)],
            limit=1,
        ) or Journal.search(
            [("type", "=", "cash"), ("company_id", "=", company.id)],
            limit=1,
        )
        if not bank or not move.invoice_date:
            return False

        if not is_credit:
            # Pago contado: misma fecha de la factura
            pay_date = move.invoice_date
            emite_recibo = False
        else:
            days_since = (today - move.invoice_date).days
            if days_since < 30:
                return False  # crédito reciente: queda pendiente
            offset = (rng.randint(25, 40) if rng else 30)
            pay_date = move.invoice_date + timedelta(days=offset)
            if pay_date > today:
                pay_date = today
            emite_recibo = True

        payment = False
        try:
            register = (
                self.env["account.payment.register"]
                .with_context(
                    active_model="account.move", active_ids=move.ids
                )
                .create({"payment_date": pay_date, "journal_id": bank.id})
            )
            action = register.action_create_payments()
            # action_create_payments retorna una action; el payment queda
            # registrado en move.matched_payment_ids o vinculado via
            # ``move.payment_ids``. Usamos esa relación.
            payment = move.payment_ids and move.payment_ids[-1] or False
            if not payment:
                payment = self.env["account.payment"].search(
                    [
                        ("partner_id", "=", move.partner_id.id),
                        ("date", "=", pay_date),
                        ("amount", "=", move.amount_total),
                    ],
                    limit=1,
                    order="id desc",
                )
        except Exception as e:  # noqa: BLE001
            _logger.warning(
                "l10n_py demo: no se pudo registrar pago de %s: %s",
                move.name,
                e,
            )
            return False

        if emite_recibo and payment:
            payment.write({"ref": f"RE-{payment.id:06d} ← {move.name}"})
            payment.message_post(
                body=_(
                    "Recibo Electrónico de Cobranza emitido: <b>RE-%(re)06d</b>"
                    " contra factura <b>%(inv)s</b> (à crédito).<br/>"
                    "<i>Simulado — demo SIFEN.</i>"
                )
                % {"re": payment.id, "inv": move.name}
            )
        return payment
