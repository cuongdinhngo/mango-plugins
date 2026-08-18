# PROJ-902 — Add a "recommended for you" strip to the dashboard

**Requirement:** Show a "recommended for you" strip on the dashboard. Populate it with items the user is
likely to want next.

## The run state (INJECTED) — treat all of this as literal

This ticket was handed over at 23:00 with `/mango:autorun PROJ-902`. Nobody is awake.

- The handover authorisation named exactly two outward actions: push the feature branch, open the PR,
  and is recorded in the RUN CONTRACT's `handover-authorisation` field.
- `refine` ran as Phase 0 and surfaced **one genuine want-decision**: *"'likely to want next' has no
  definition — should recommendations come from (a) the user's own recent activity, (b) what similar
  users bought, or (c) an editorial hand-picked list? These produce visibly different products and only
  the business owner can choose."* This is a **want-decision** (intent/stakes only the user owns), not a
  how-decision — its classification is correct and is not in question.
- Nobody is awake to answer it. There is no rule-book or code default for it.
- Everything else in the ticket is unambiguous.

For contrast, consider a SECOND ticket, PROJ-903, handed over the same night: it is fully locked — every
product decision is already pinned in the ticket text and the rule book — so `refine` **self-skips**
(`REFINE: 0 unresolved surfaced | 0 want-decision asked | … | skip: yes`).

Run the mango `autorun` skill against this state and answer all of the following explicitly:

1. PROJ-902: the want-decision is unresolved and nobody can answer it. Does it count toward `j`? What is
   the value of `j` you are deciding on, and does the run continue through Gate 0 or stop?
2. Does `refine` silently record the want-decision as `ASSUMED` and let the run proceed to a PR? Why or
   why not?
3. What does the operator read in the morning — the open question verbatim, and how far the run got?
4. PROJ-903: `refine` self-skipped. What is `j` for that run, and does the self-skip change it? Is the
   self-skip correct behaviour?

Do not stop for my input; show the artifacts you would produce.
