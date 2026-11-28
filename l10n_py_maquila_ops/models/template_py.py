# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("py", "account.fiscal.position")
    def _get_py_maquila_account_fiscal_position(self):
        """Provide the "Maquila - Exportacion Exenta" fiscal position, with
        its IVA -> exonerado tax mapping, as chart template data for the
        'py' template.

        This makes the position (and its per-company tax mapping) available
        for every company that loads the 'py' chart, generated the same way
        as the rest of the chart's fiscal positions in ``l10n_py`` — instead
        of being created on the fly (with ``sudo()``) from a sale order
        onchange, which is never allowed to write to the database.
        """
        return self._parse_csv(
            "py", "account.fiscal.position", module="l10n_py_maquila_ops"
        )
