# PROJ-905 — Record the drift list after the error-handling standard is chosen

**Requirement:** `codify` has already counted the observed patterns and the human has **chosen** the
going-forward error-handling standard. The chosen standard is now recorded as `PROVISIONAL (awaiting
ratification)`, and a **drift list** of files diverging from it is being emitted as follow-up tech-debt.

## Context — the near-miss this catches

The drift entries observed are:

| # | File | Diverges by |
|---|------|-------------|
| 1 | `src/handlers/orders.ext` | bare re-raise, no context |
| 2 | `src/handlers/invoices.ext` | swallows the error |
| 3 | `src/jobs/export.ext` | logs and continues |
| 4 | `src/jobs/import.ext` | swallows the error |
| 5 | `src/lib/http.ext` | bare re-raise, no context |

They roll up into **2** follow-up tech-debt tickets (handlers, jobs+lib).

In a field run this count was reported as **prose** — "about six files drift" — where the list actually
held five. A prose count is fudgeable in a way the other counted artifacts (`REFINE:`, `BREAKDOWN:`,
`SECTIONS:`) are not.

Emit the drift-list step's output exactly as `codify` specifies it, including the counting line and its
numbers. Do not stop for my input.
