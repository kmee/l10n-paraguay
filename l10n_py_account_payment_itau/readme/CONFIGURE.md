On a bank account (Contactos > a Company's res.partner.bank, or Accounting
> Configuration > Bank Accounts), enable "Banco Itaú (Open Banking)" and
fill in:

- Entorno (Testing / Producción) -- both require a URL provided by the
  bank; there is no public, confirmed sandbox host to default to.
- RUC de la Empresa and Código de Empresa, as shown on the "24 Horas
  Negocios" portal.
- Certificado mTLS (PEM) and Clave Privada mTLS (PEM), obtained via
  "Open Banking > Suscripción al canal > Solicitar certificado mTLS" on
  the bank's portal.
- Token de Canal (placeholder -- see this module's known gap; leave
  empty until Fase 3 confirms whether/how it is used).

All of the fields above are restricted to the Accounting Manager group.

Obtaining channel access itself (RUC-based login, iToken administrador,
IP whitelist, digital subscription acceptance) is a business/onboarding
process handled entirely on the bank's own portal -- out of scope for
this module and for the Odoo configuration above.
