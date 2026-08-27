# PROJ-522 — Return 409 when a duplicate import is submitted

**Requirement:** submitting an import whose checksum already exists returns HTTP 409 with the code
`duplicate_import`.

**Acceptance Criteria:**
- AC1: a duplicate submission returns status `409`.
- AC2: the response body's `code` field is exactly `duplicate_import`.
- AC3: the retry-after header is absent on a 409 (it applies only to 429).

## The design state (INJECTED) — treat all of this as literal

Assume Gate 1 cleared. `.harness.json` has **no `real_corpus_path` key at all**. The proposed proving
test is an integration test hitting the endpoint twice and asserting the status, the body code, and the
absent header.

A second, unrelated ticket in the same project has an AC reading *"the duplicate-detection heuristic
groups near-identical imports sensibly"*; its design recorded that AC as `authored` plus a coverage-gap
exclusion carrying `expiry: PROJ-540 (the corpus ticket)`.

Run the mango `design` skill against this state and answer all of the following explicitly:

1. What is the fixture provenance of AC1, AC2 and AC3, and why?
2. Does this ticket need a real corpus? Does the missing `real_corpus_path` key add any step, warning
   or block to this ticket?
3. For the second ticket's exclusion — `authored` plus an exclusion with `expiry: PROJ-540` — does that
   count as recorded, and does Gate 2 close?
4. Emit the `EXCLUSIONS:` counted line for THIS ticket.

Do not stop for my input; show the artifacts you would produce.
