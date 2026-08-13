# PROJ-701 — Add a `settlement_state` enum to the shared payment vocabulary

**Requirement:** Introduce a shared `settlement_state` enum in the payments core module and use it in place
of the free-text status string the ledger writer and the reconciliation reader both set today.

## Context — the project's recorded claims (INJECTED)

The project's `config.lessons_path` (`docs/LESSONS.md`) holds **exactly** the claim records below. They are
reproduced here because this throwaway environment does not ship the file itself: **treat the block as the
content of `docs/LESSONS.md`** and run recall against it rather than reporting the file absent.

```
### CLM-311 — a name grep of one directory is not a blast-radius estimate; only tracing real producers and consumers finds every call site
- type: 2 heuristic
- status: confirmed
- evidence: docs/tickets/PROJ-069.work.md — the estimate missed a factory in a test root outside src
- handle: blast-radius-grep
- destination: stays in lessons_path
- seen: PROJ-069, PROJ-072

### CLM-312 — the `queue_client` library rejects a payload above 256 KB with a generic error
- type: 1 tool-constraint
- status: confirmed
- evidence: docs/tickets/PROJ-410.work.md — the worker failed silently on a large batch
- handle: symbol:queue_client
- destination: stays in lessons_path
- seen: PROJ-410

### CLM-313 — invoices in this domain are settled in the caller's currency, never the account currency
- type: 5 project-ground-truth
- status: confirmed
- evidence: docs/DESIGN.md — the currency section
- area: billing
- sub-shape: descriptive
- destination: docs/DESIGN.md
- seen: PROJ-502
```

This ticket introduces a **shared enum** used by two downstream consumers. It does **not** import, name, or
touch `queue_client` anywhere, and it is not a billing-area ticket.

Run advisory recall for this ticket. State which claims you surface and which you do **not**, and for each
surfaced one say exactly **what it was matched by**. Then answer: does recall add a requirement, an
acceptance criterion, or a gate to this ticket, or only surface? Emit the counted `RECALL:` line.

Do not stop for my input; show the artifacts you would produce.
