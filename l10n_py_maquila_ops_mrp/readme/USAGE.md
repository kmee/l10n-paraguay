1. Install both ``l10n_py_maquila_ops`` and ``l10n_py_maquila_mrp``; this
   module installs itself automatically.
2. Open the **TUM 1%** wizard from a program with an analytic account
   configured, and run **Compute**. The VAN fields (national, Mercosur and
   imported cost, and the VAN amount) are filled in alongside the export
   invoice amount, and the TUM base uses whichever of the two is higher.
3. If the selected period has no completed manufacturing order, the VAN
   fields stay at zero and a warning is shown; the TUM base then uses the
   export invoice amount only.
