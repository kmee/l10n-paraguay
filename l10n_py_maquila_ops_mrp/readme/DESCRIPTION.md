Bridge module between Paraguay's Maquila operations and MRP modules
(``l10n_py_maquila_ops`` and ``l10n_py_maquila_mrp``):

- Auto-installs when both modules are present, so no manual configuration is
  needed to link them.
- The TUM base keeps the value added of Ley 7547/2025 Art. 37, computed by
  ``l10n_py_maquila_ops`` from the accounting (goods and services acquired in
  the country, salaries with social security, depreciation and the maquila
  service remuneration).
- This module adds to the **TUM 1% wizard**, for information, the origin split
  of the inputs consumed by the completed manufacturing orders of the period
  (national, Mercosur and imported cost, and the national content), via the
  shared ``_maquila_van_for_period`` method of the program used by the VAN wizard
  and the CNIME report. The amounts are converted to the currency of the wizard.
- Without an analytic account on the program or a completed manufacturing
  order in the period, the split stays at zero and a notice is shown. It never
  changes the TUM base.
