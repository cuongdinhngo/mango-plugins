# PROJ-908 — Trim trailing spaces on the search query

**Requirement:** A search query with trailing spaces returns the same results as the trimmed query.

**Acceptance Criteria:**
- Searching `"widget "` returns the same results as `"widget"`.

## Round-1 review outcome (already run)

Round 1 dispatched the `reviewer` + the ticket-blind `challenger`. The challenger rebuilt the
requirement and found it **met**; the proving test passed and the baseline was green. The reviewer
returned a **conditional LGTM** — *"LGTM once findings 1–2 land as described"*:

1. `src/search/query.js:14` — trim before the cache-key is built, not after.
2. `src/search/query.js:22` — reuse the trimmed value in the empty-query guard.

The author applied exactly those two fixes to `src/search/query.js` and nothing else — the fixes stay
**inside the already-named findings**; **no fix changed scope**.

## What round 2 must do (main-loop-by-default verify-only)

This fixture exercises **how** the verify-only re-review is carried out. Because the fixes are in-scope,
round 2 is a **verify-only pass done in the main loop, dispatching no subagent**: confirm findings 1–2
are present as described by inspection, re-run **only the affected proof**, and run a regression scan
over the Phase-1 callers — **without** re-dispatching a reviewer or a challenger. That is the explicit
default so the cost does not swing on operator choice.

State exactly **how** round 2 verifies — in the main loop or by re-dispatching a reviewer/challenger —
and state **what would trigger a re-dispatch** (a fix that changed scope: touched a file outside the
approved set, or introduced a new surface/behaviour beyond the named findings). Do not stop for my
input.
