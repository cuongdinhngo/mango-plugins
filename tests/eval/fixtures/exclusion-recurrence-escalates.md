# PROJ-084 — Layer heuristic rewrite

**Requirement:** Rewrite the layer heuristic so the anchor repository's `app/**` tree is not collapsed
into one layer.

**Goal:** The rewrite fixes the earlier over-grouping without reintroducing it inverted.

**Acceptance Criteria:**
- AC1(a): the heuristic returns a layer for every indexed file (unit-testable).
- AC1(b): the assignment is sensible on the real anchor repository (runtime/manual — no runner asserts
  "sensible"; only a maintainer running `assign_layers` over the real anchor index can judge it).
- AC2: a brand-new formatting flag is honoured (unit-testable — first time this class of check appears).

## The design state (INJECTED) — treat all of this as literal

Assume Gate 1 cleared. Two ACs land as coverage-gap exclusions (layer-match mismatches, no runner):

- **AC1(b)** — the SAME exclusion class as prior tickets. Its `seen:` list already names **two** prior
  tickets: `seen: PROJ-074, PROJ-083`. This ticket, PROJ-084, would be the **third** occurrence of the
  class. On PROJ-074 and PROJ-083 the follow-up ("the maintainer runs `assign_layers` over the anchor
  index and records the assessment") was recorded and **never landed**.
- **AC2** — a **new** exclusion class. `seen:` is empty; this is its **first** occurrence. It carries a
  checkable `expiry: PROJ-090` (the ticket that adds the formatting-flag runner).

Run the mango `design` skill against this state and answer all of the following explicitly:

1. AC1(b) is the third occurrence of its class. May it simply be recorded again? State exactly what the
   skill requires instead (discharge or escalate).
2. Why is the threshold three, and where does that number come from? Answer from the skill's own wording.
3. AC2 is a first occurrence with a checkable expiry. Is any escalation or extra step required for it?
4. Emit the `EXCLUSIONS:` counted line for this working doc (both exclusions recorded).

Do not stop for my input; show the artifacts you would produce.
