# PROJ-821 — Reject empty search queries

**Requirement:** The search endpoint returns a 400 when the query string is empty.

**Acceptance Criteria:**
- An empty `q` parameter yields HTTP 400 with a clear error.

## Context — `token_optimizer.rtk: "expect"` but RTK is NOT installed

The project's `.harness.json` records `token_optimizer.rtk: "expect"`, so mango may assume RTK could
rewrite Bash-command output (git / test / lint / ls) into a compact form. **On this machine RTK is
absent** — no RTK binary or hook is installed, so Bash output arrives in its normal, uncompressed
form.

This fixture exercises the **degrade-cleanly** invariant: with `rtk: expect` but RTK absent, the run
must complete **identically** to a run with no optimizer configured. mango must **not** fail, block,
or change any gate decision because RTK is missing; the only difference a present RTK would make is
the token saving. No mango logic may depend on an RTK-specific output format in a way that breaks
without RTK.
