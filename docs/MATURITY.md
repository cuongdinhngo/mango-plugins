# Maturity — detail

The short version is in the [root README](../README.md#maturity): every release is gated by
`validate.py` and the dispatch-free script suites, and mango has **no behavioural regression suite**
— only a per-skill smoke guard. This page holds the record behind that summary. Which behaviours are
**Experimental** is tracked only in
[`plugins/mango/principles/maturity.md`](../plugins/mango/principles/maturity.md).

**Why the suite was retired (1.16.0).** The 126-job behavioural suite that preceded it produced 30
reds over its whole life, of which **zero** were mango behaving wrongly: 12 were assertion wording,
10 were defects in the eval harness itself, 7 were environment, 1 was a fixture. It never caught a
cross-skill regression. Over the last 60 days it absorbed 86 commits against 25 to the behaviour
directories. Every defect it did find was a defect in itself; every defect found in mango's behaviour
was found by probing real data, by review, or in the field. The counts above are tabulated in the
1.16.0 entry of [`plugins/mango/CHANGELOG.md`](../plugins/mango/CHANGELOG.md), and the cycle records and
harness defects they were read off — every one with the method that found it — are kept in
[`tests/eval/history/`](../tests/eval/history/), so the decision is auditable rather than repeated.

The public skill/config API has been stable since 1.0 **with one exception, in 1.14.0**: the `RUN
CONTRACT`'s `force-broken` / `force-holding` condition fields and `reconcile.py --prove` are removed.
Three field runs measured the forced-case control inert — every condition reported `FORCE-UNPROVEN` —
so it was retired rather than left as ceremony. A contract carrying either field is rejected with a
named reason, and `--prove` is refused rather than silently ignored.

Though written for Claude Code, mango is not locked to it: it has run its full lifecycle on other
hosts — including Cursor, driving real tasks to merged pull requests on a production codebase, with a
different underlying model.

The **unattended lane** (`/mango:autorun`, 1.11.0) is marked **Experimental**: its gate conditions are
the shipped, field-tested ones, and it has now driven real tickets to a pull request unattended — what
stays Experimental is the exact condition set a `RUN CONTRACT` should carry and the call-count budget
proxy — with one part of the condition set now settled and removed: the forced-case positive control
was measured inert across three runs and is retired. Its safety boundaries are not Experimental — no gate is removed, the review seat is never degraded
away, and there is no auto-merge.

The **counted-line checker** (`scripts/check_lines.py`, 1.13.0) is the newest surface. That the harness
parses a counted line rather than its author reading it is settled and is the point; **Experimental** is
the grammar registry's tolerance boundary — which spellings are inflection and which are a paraphrase.
Its safety boundaries are not Experimental: it reports and never rewrites, `not-checkable` is never a
pass, it adds no counted line of its own, and where it cannot run the run says so instead of claiming to
have checked.

**Evidence provenance** (1.14.0) is the newest surface on it: test evidence records the SHA of the tree
it ran against — for a containerised suite, the tree the **image was built from** — and a gate refuses
evidence from a different tree, reusing the stale-review guard's rule rather than building a second one.
Settled and not Experimental: `provenance-unknown` is a third state and never a pass, and an axis the
caller did not ask for is reported as absent rather than as clean. **Experimental** is how much of a
project's evidence the marker reaches: it binds the shipped `$ <command>` empirical-output shape, and
evidence recorded in some other shape is counted `provenance-unknown` rather than silently skipped.

The **delegation dispatch** (1.17.0) is the newest surface: `execute` hands implementation to the
Sonnet `implementer` agent and `analysis` fans out to the Sonnet `explorer` agent. That these rows are a
choice of agent is settled; **Experimental** is the split itself, since neither agent has yet run on a
real ticket. Its safety boundaries are not Experimental: a high-stakes change stays on the main loop,
every `implementer` STOP escalates and is never re-dispatched, and not dispatching is recorded in the
Cost ledger.
