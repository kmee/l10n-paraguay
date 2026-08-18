1. On **Contacts > Configuration > Banks** (``res.bank``), set the
   **Código de Banco SIPAP** and, once an exporter module is installed,
   the **Formato de Exportación SIPAP** (e.g. ``iso20022``) for each bank
   that will receive a batch file.
2. On a bank account (``res.partner.bank``), optionally set the **Tipo
   de Alias CAS** and **Alias CAS** (phone/email/RUC/CI) if the
   beneficiary is to be identified by an alias instead of a full account
   number.
3. Create an **Account Payment Method Line** on the relevant bank
   journal using the **SIPAP Batch File** payment method (Accounting >
   Configuration > Payment Methods).
