# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Load the "Maquila - Exportacion Exenta" fiscal position (and its
    tax mapping) for companies that already had the 'py' chart of accounts
    loaded before this module was installed.

    Companies that install/load the 'py' chart *after* this module is
    installed already get the position through the
    ``@template("py", "account.fiscal.position")`` data registered in
    ``models/template_py.py``, which chart loading picks up automatically.
    """
    chart_template = env["account.chart.template"]
    companies = env["res.company"].search([("chart_template", "=", "py")])
    for company in companies:
        data = chart_template._parse_csv(
            "py", "account.fiscal.position", module="l10n_py_maquila_ops"
        )
        if not data:
            continue
        chart_template.with_company(company)._load_data(
            {"account.fiscal.position": data}
        )
