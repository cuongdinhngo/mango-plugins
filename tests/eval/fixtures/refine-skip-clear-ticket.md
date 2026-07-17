# PROJ-710 — Add a CSV export button to the orders list

**Requirement:** Add an "Export CSV" action to the orders list page, matching the existing
"Export CSV" actions already shipped on the invoices list and the customers list.

## Context

The project already ships a repeated, established pattern: every list page exposes an "Export CSV"
action wired the same way (same button placement, same column-from-table derivation, same filename
convention). This request is the **Nth item following that existing repeated pattern** — the orders
list is simply the next list to receive the same action. A project scan (README + the two existing
implementations) answers every "how" question by citation, and there is **no genuine product-WANT** the
convention does not already settle.

This fixture exercises refine's **self-skip**: 0 unresolved product-decisions → refine SKIPS (records
"0 unresolved product-decisions") and hands to analysis, WITHOUT fabricating a loại-A question (no
over-trigger). refine must not be a tax on a clear, convention-covered ticket.
