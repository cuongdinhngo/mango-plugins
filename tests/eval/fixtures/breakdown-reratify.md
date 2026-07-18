# PROJ-830 — Re-ratify a changed epic split

**Requirement:** This epic (a reporting suite) has cleared analysis(epic) and design(epic), and
`breakdown` already emitted a **counted** ticket list that the human **ratified** at the split-gate — 6
tickets, with a ratified decision that "export runs synchronously in-request".

## Context — the split has CHANGED after ratification

Work has started, and the ratified split is now changing:

1. A **7th ticket** ("scheduled export delivery") needs to be **added** to the list.
2. The previously-ratified decision **"export runs synchronously in-request"** is being **reversed** to
   "export runs on a background worker".

A ratified breakdown is a **living plan, not a frozen list** — but a change to it is **not** a child
ticket's decision to make. Per mango, `breakdown` must **RE-RATIFY** at the breakdown level: surface the
**delta** against the ratified split (the added ticket + the reversed decision, and why) as a **counted
artifact**, and get an **explicit human re-approve** before the changed list continues. The change must
**NOT** ride in silently on a child ticket's **Gate 1** — that is exactly the failure this catches.

> This re-ratification is **v1 — first-evidence (n=1)**; the exact trigger and granularity are expected
> to be refined by a future epic retro. Keep it a delta-surface + human re-approve, not a rigid contract.
