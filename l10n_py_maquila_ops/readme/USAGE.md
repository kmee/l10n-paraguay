1. Register a **customs guarantee** for the program.
2. Create a **temporary admission** with its CIF amount and lines; admitting it
   checks the CNIME certificate and that the guarantee covers the CIF (converted
   to the guarantee currency). Use *Extend 12 Months* for the Art. 14 extension.
3. Create an **export** and link it to its source admissions before confirming.
4. On the program, tab *Single Tax (TUM)*, set the salary and depreciation
   accounts and the TUM expense and payable accounts.
5. Every month, create a **TUM Monthly Declaration** (Maquila > Fiscal), run
   *Compute*, add manual lines for what has no accounting source (for
   example salaries without payroll, with the payroll reference as support),
   *Confirm* (also when there were no exports), print the summary and
   generate the journal entry. The value added comes from:

   - a) and b): posted vendor bills of suppliers of the company country,
     goods and services (lines without product count as services);
   - c) and d): journal items on the program salary and depreciation
     accounts;
   - e): posted customer invoices of service products;

   always limited to entries that carry the program or lines distributed to
   the program analytic account (by its percentage).
6. Use the **IVA credit** wizard to compute and post its entry.

The two fiscal positions shipped in this module (temporary admission and exempt
export) carry no tax mapping: the actual IVA/customs tax mapping depends on the
chart of accounts in use and is left to the integrator.
