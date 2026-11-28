1. Go to *Maquila > CNIME Reports* and create a report for a program and
   period.
2. Press *Generate* to compile the snapshot (imports, exports, production,
   waste, period-end stock balance, VAN, employment).
3. Validate and submit. A submitted report can no longer be regenerated or
   reset to draft.
4. Optionally generate the SIMEX payload for offline presentation.

Generating the SIMEX payload/attachments and submitting the report are
restricted to the *Maquila Manager* group; the *Maquila User* group has
read-only access and cannot perform either action. There is no automatic
submission to the SIMEX/VUE portal: pressing *Submit* only records, via the
submission protocol, that the manual submission was already done outside
Odoo. Regenerating the SIMEX payload while the report is *Validated*
replaces the two previous ``simex_*`` attachments; once the report is
*Submitted*, generation is blocked because the payload that was actually
sent must stay frozen. The Art. 13 periodic report layout (Decreto
5714/2026) is out of scope for this version, pending the Secretaría
Ejecutiva's resolution.
