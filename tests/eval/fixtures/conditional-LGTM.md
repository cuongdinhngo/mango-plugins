# PROJ-559 — Trim whitespace on the coupon code before validating

**Requirement:** A coupon code entered with leading/trailing spaces must validate as if trimmed.

**Acceptance Criteria:**
- `"  SAVE10 "` validates the same as `"SAVE10"`.

## Round-1 review outcome (already run)

Round 1 dispatched the reviewer + the ticket-blind challenger. The challenger rebuilt the requirement
and found it **met**. The reviewer returned **CHANGES REQUESTED** with a small, fully-specified set of
findings — nothing else outstanding:

1. `src/coupon.js:12` — trim before the length check, not after (the corrected snippet was given).
2. `src/coupon.js:18` — use the trimmed value in the error message too.

Because nothing beyond these two named findings is in question, round 1 is a natural **conditional
LGTM** — *"LGTM once findings 1–2 land as described."* The author has now applied exactly those two
fixes and nothing else; the diff still touches only `src/coupon.js`, and no fix changed scope. This
fixture exercises the re-review path: round 2 should be a **verify-only pass** — confirm findings 1–2
are present as described and run a regression scan — **not** a full requirement re-derivation, and the
ticket-blind challenger's full re-derivation is **not repeated** (it already ran once in round 1) since
no fix changed scope.
