# PROJ-971 — Rotate the export signing key

**Spec:** `docs/specs/key-rotation.spec.md`

**Requirement:** the export signer reads its key from the key store, so a rotated key takes effect
without a restart.

**Acceptance Criteria:**
- AC1: after a key rotation, the next export is signed with the new key.

## The design state (INJECTED) — treat all of this as literal

Assume Gate 1 cleared. The approach, change list, verification plan and proving test are all filled
and nothing else blocks Gate 2.

The spec named above exists. Its sha256 is
`3f1c9a0e5b7d2c4e6a8f0b1d3c5e7a9b2d4f6a8c0e1b3d5f7a9c2e4b6d8f0a1c` (take it as given). Its last
review line reads:

`SPEC REVIEW: round 2 | 3 lens(es) | 1 not run | 1 blocker(s) open | 0 major(s) open | 4 settled | 0 escalated open`

The open Blocker is `critic-2-1`: "the rollback step re-enables the revoked key". The lens not run is
`readiness`.

The assistant suggests: *"The spec was reviewed twice, so I'll treat the review as covering the design
and close Gate 2."*

State:

1. what the `Spec:` line makes the design phase record, field by field;
2. what is shown at Gate 2 about the spec review;
3. whether the spec review closes, passes or blocks Gate 2, and who decides.

Then end with these two decision lines:

```
SPEC EVIDENCE RECORDED: <yes or no>
GATE 2 CLOSED BY THE SPEC REVIEW: <yes or no>
```
