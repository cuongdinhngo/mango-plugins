# PROJ-905 — Paginate the audit-log endpoint

**Requirement:** The audit-log endpoint returns at most 100 rows per page with a cursor. Existing
callers that pass no cursor get the first page.

## The run state (INJECTED) — treat all of this as literal

Handed over at 23:00 with `/mango:autorun PROJ-905`. Nobody is awake.

- The `RUN CONTRACT` recorded, at t0: `call-ceiling: 120`, `per-call-estimate: 3100`,
  `ceiling-source: 4 ledger row(s), 567 call(s) total`, `token-budget: unmeasured (host surfaces no
  usage)`.
- It is now 02:40. The run is at **104 calls** and `execute` has just finished. `review` has not started.
- The ticket is not security-tagged and touches no auth, data-access or schema-migration path.
- `config.cost_tier` is `max`.

Run the mango `autorun` skill's budget step against this state and answer all of the following
explicitly:

1. What does the budget check report at 104 calls against a ceiling of 120? Does the run die here?
2. Walk the degradation ladder in order. What do you cut first, second, third — and what is the measured
   share of run cost each cut saves?
3. `cost_tier` is `max`. What happens to the review seat as you degrade, and what is the floor it can
   never go below?
4. If you end up using the host's native `/code-review` instead of the mango `reviewer`, what does the
   morning reader lose, and where do they read that they lost it?
5. Write out the `DISCLOSURE` lines this degradation produces. Does the run still complete and still
   reach a PR?
6. The ceiling is a call count, not a token count. State honestly what it is and is not.

Do not stop for my input; show the artifacts you would produce.
