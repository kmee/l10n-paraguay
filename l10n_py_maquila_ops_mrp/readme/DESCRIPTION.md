Bridge module between Paraguay's Maquila operations and MRP modules
(``l10n_py_maquila_ops`` and ``l10n_py_maquila_mrp``):

- Auto-installs when both modules are present, so no manual configuration is
  needed to link them.
- Extends the **TUM 1% wizard**'s ``action_compute`` to also compute the VAN
  (national added value) for the period, via the program's shared
  ``_maquila_van_for_period`` method, so the TUM and VAN wizards always
  report the same figures for the same program and period.
- The VAN amounts (``total_cost``, ``national_cost``, ``mercosul_cost``,
  ``imported_cost``, ``van_amount``) are stored in the company currency by
  ``_maquila_van_for_period`` and are converted to the wizard's currency
  before being displayed.
- If there is no completed manufacturing order in the period, the origin
  split of the cost cannot be determined: the VAN is left at zero, a warning
  is shown on the wizard, and the TUM base falls back to the export invoice
  amount only (the same behavior as without this module installed). A
  missing analytic account on the program is still a blocking configuration
  error.
