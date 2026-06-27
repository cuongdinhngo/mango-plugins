<!-- UI-PROOF-SCAFFOLD TEMPLATE. `execute` uses this to produce a TIER-1 `PASS(automated)` proof
WITHOUT mango owning a stack. It is a runner-agnostic SHAPE, not a runner: it names NO test-runner,
library, or framework API (HARD RULE — mango is public and general-purpose). Compose the PROJECT's
declared automated-UI runner; if none is declared, mango does NOT bundle one — it drops to a tier-2
recorded render proof (see the proof-tier ladder), it never stops. This scaffold defines tier-1 only
(the automated-proof contract C1–C8); tier-2 render proofs follow the lighter render-proof contract. -->

# Tier-1 automated UI/a11y proof — generic scaffold

A `PASS(automated)` entry in the proof manifest must satisfy the automated-proof contract **C1–C8**.
Produce it by composing the project's declared automated-UI runner into this shape — one proof per
affected surface, asserting that surface's measurable threshold against a **real rendered DOM**.

## The shape (five parts)

1. **Boundary seam (C1 + C2).** Stub **only** the un-automatable edge (the outermost network / device
   / time boundary) **before app code evaluates it**. The system under test stays **real** — never
   mock the component/view being proven. If you find yourself mocking the thing the AC is about, the
   proof is invalid.
2. **Per-test state reset (C8).** Reset all shared state between tests, and pin any non-deterministic
   input (clock, randomness, network timing) so the proof is **deterministic** — same result every run.
3. **Drive by role + accessible name (C5).** Locate and operate elements by their **role + accessible
   name**, not by internal/non-semantic selectors. This doubles as a11y evidence. A non-role selector
   is allowed only with a **recorded reason** in the manifest row — otherwise the reviewer flags it.
4. **Assert the exact threshold (C3).** Assert the gate's **measurable value** (e.g.
   `scrollWidth ≤ clientWidth`, computed `font-size ≥ 16px`, target box ≥ size, focus indicator
   present at ≥ 3:1) — never "looks ok". Each AC is discharged at **exactly one** layer matching its
   risk (C6 — no double-count). An uncovered branch becomes a **recorded exclusion** (C7), never a
   silent gap.
5. **Re-runnable command + artifact (C4).** Emit **one command** the reviewer/challenger can re-run
   and an **inspectable artifact** (report/output) it produces. Record both in the manifest row's
   `proof-cmd|artifact` field.

## Pseudo-shape (illustrative only — no runner API)

```
proof for (AC <id> × surface <route/overlay/modal/state>):
  setup:
    reset shared state                      # C8
    pin clock / randomness / network        # C8
    stub ONLY the outermost boundary         # C2 (SUT stays real — C1)
  render the REAL affected surface at <breakpoint>
  locate target by role + accessible name    # C5
  assert <measurable threshold>              # C3 (one layer only — C6)
  teardown leaves an inspectable artifact     # C4
# invoked by ONE re-runnable command          # C4
```

When the project declares no automated-UI runner, do **not** scaffold tier-1 — record a tier-2
`PASS(render@<bp>)` (a recorded render/screenshot of the real surface at the breakpoint, asserting the
visible measurable) instead. A proof is mandatory at some tier; only the tier is elastic.
