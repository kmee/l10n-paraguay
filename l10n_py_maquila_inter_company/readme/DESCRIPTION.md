Glue between the OCA inter-company modules (`purchase_sale_inter_company`,
`account_invoice_inter_company`) and the Paraguayan maquila regime, for a
group where the foreign matrix (for example a Brazilian company) and its
Paraguayan maquiladoras live in the same database.

The maquila rule only looks at the data (a maquiladora selling to a partner
that is another company of the database) and lives in methods of
`sale.order` and `account.move`. The hooks of the OCA inter-company modules
are thin triggers, so a sale order typed by hand for the matrix, or created by
another inter-company engine, gets the same values.

When the matrix confirms a purchase order to a maquiladora (or a sale order
to the matrix company is created in the maquiladora):

- the sale order created in the maquiladora is linked to the active maquila
  program whose foreign matrix is the buying company (and therefore to its
  CNIME contract). When several programs match, the one listing all the
  ordered products wins;
- the order keeps the export fiscal position resolved by the Paraguayan
  chart for a foreign partner (VAT mapped to Exonerado), or falls back to it
  explicitly when nothing was resolved. A fiscal position configured on the
  partner is never replaced;
- the Incoterm of the purchase order is copied to the sale order, so it
  reaches the export invoice;
- when the order is confirmed, a note is posted if no program was found or
  if some products are not listed in the program.

When the maquiladora posts the export invoice, the vendor bill created in
the matrix keeps the currency and the Incoterm, uses the Paraguayan document
number as bill reference, shows the document number and the SIFEN CDC of the
source document, and stores on each line the NCM code declared by the
supplier.
