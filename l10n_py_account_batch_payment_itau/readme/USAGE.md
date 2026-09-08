Create a SIPAP batch payment order (payment method ``SIPAP Batch File``)
whose company bank account's ``res.bank`` is configured as described in
CONFIGURE.md, then confirm/generate the payment file as usual.

Today this always raises a clear error explaining that the real Itaú
API dispatch is pending Fase 3 of the integration plan -- it does not
silently do nothing, and it does not fabricate a fake successful
dispatch.
