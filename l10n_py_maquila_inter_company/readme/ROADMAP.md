- The program of the sale order is not propagated to the invoice by
  `l10n_py_maquila_ops`; until it is, set it on the export invoice so that
  the TUM wizard finds it.
- The CDC shown on the vendor bill only exists after the document is sent to
  SIFEN.
- The NCM is stored as text. A Brazilian localization (`l10n_br_fiscal`)
  would map it to its own NCM record; that mapping is not done here.
- Only the purchase to sale direction exists in the OCA inter-company
  modules; a sale order created first in the maquiladora does not create
  the purchase order of the matrix.
- Companies in different databases are out of scope.
- The rule methods (program, fiscal position, values kept on the vendor bill)
  belong to `l10n_py_maquila_ops`; once it is merged they can move there,
  leaving in this module only the bridge with the OCA inter-company modules.
