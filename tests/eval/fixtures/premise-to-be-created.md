# PROJ-781 — Add a monthly report exporter

**Requirement:** Add a **new** monthly report exporter that writes the month's rows to CSV.

## Context

Create a new module at `src/reports/exporter.js` to hold the exporter, and add its proving test as a
new spec at `spec/reports/exporter_spec.js`. Nothing like either file exists yet — this is net-new
work. The CSV columns are the four listed here: month, account, units, total.

**The references in this ticket are claims about THIS checkout** — resolve them against it.

This fixture is the **negative control** for the premise check: every path the ticket names is framed
as **to be created**, so its absence from the checkout is expected and correct. The premise check must
**not** halt the phase — it must record zero missing references and let refine carry on with its normal
Phase-0 work. A guard that fires on a file the ticket exists to create would block every net-new
ticket.
