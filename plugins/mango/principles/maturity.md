## Maturity — Stable vs Experimental

Every shipped behaviour carries an honest maturity level so a reader knows what is settled:

- **Stable** — committed behaviour, field-tested, safe to rely on. This is the default for everything
  not marked otherwise.
- **Experimental** — works and has been validated, but its exact shape may still change until further
  real-world use. Marked explicitly at the behaviour.

Eight behaviours are **Experimental** today:

- **the unattended lane (`autorun`) and its three envelope artifacts.** The gate conditions it closes on
  are the shipped ones and are Stable; what is Experimental is the unattended closing itself, the exact
  condition set a `RUN CONTRACT` should carry, and the call-count budget proxy. Its prediction is
  falsifiable on one real overnight ticket: a ticket handed over at 23:00 reaches a PR by morning with
  one human touch remaining — the merge — and `RECONCILE` reports the state of the world after the last
  push without being asked. **Its safety boundaries are NOT Experimental** and never will be: no gate is
  removed, the review seat is never degraded away, there is no auto-merge, `j > 0` stops the run, and no
  outward action happens beyond the two the handover authorisation named.

- **the counted-line checker's grammar registry and its three checks.** That a counted line is parsed
  by the harness rather than read by its author is Stable and is the point. What is Experimental is the
  registry's exact tolerance boundary — which spellings are inflection and which are a paraphrase — and
  the sum rules that are derived from an exhaustive partition rather than stated verbatim in a skill.
  Both will move as more real working docs run through it. **Its safety boundaries are NOT
  Experimental**: it reports and never rewrites, `not-checkable` is never a pass, it ships no counted
  line of its own, and the checker's own absence never blocks a run and never reads as clean.

- **the reach of the evidence-provenance marker.** That test evidence carries the SHA of the tree it ran
  against, and that a gate refuses evidence from a different tree, is Stable — it is the stale-review
  guard's own rule pointed at a second artifact. What is Experimental is how much of a project's
  evidence the marker reaches: it binds the shipped `$ <command>` empirical-output shape, so evidence
  recorded in some other shape is counted `provenance-unknown` rather than silently skipped, and where
  a container's build tree can be established varies by project. **Its safety boundaries are NOT
  Experimental**: `provenance-unknown` is a third state and never a pass, and an axis the caller did not
  ask for is reported as absent rather than as clean.

- **breakdown re-ratification** (surfacing a post-gate split delta for an explicit human re-approve):
  validated once in the field, its re-ratification trigger and granularity may change until a second
  epic exercises it.
- **the learning loop's classification and promotion machinery** — where the six-type boundaries fall,
  which recall key each type gets, and how a recurrence is scored. It is built on three probe rounds over
  real lesson files, but its *shape* will move as more lesson files run through it. **Its five invariants
  are NOT Experimental** and never will be: the classifier proposes and the human confirms, recall is
  advisory, falsification precedes ratification, lessons never modify mango, and everything is
  project-local. Those are safety boundaries, not a shape to be tuned.
- **the delegation dispatch (`implementer`, `explorer`).** That the implement and explore rows of the
  routing map are a choice of agent pinned by frontmatter is Stable — it is the mechanism `review`
  already uses for `reviewer` / `reviewer-max`. What is Experimental is the split itself: which steps
  `execute` hands to `implementer`, what the dispatch carries, and what the `explorer` fan-out returns.
  Neither agent has yet run on a real ticket. **Its safety boundaries are NOT Experimental**: a
  high-stakes change is implemented on the main loop, every `implementer` STOP is an escalation and is
  never re-dispatched, the main loop keeps the verification sweep and the write-back, and not
  dispatching is recorded in the Cost ledger, never silently.
- **tracker local mode (`"tracker": { "mode": "local" }`).** That a project with no tracker runs from
  ticket files in `tickets_dir` is Stable in intent; what is Experimental is the exact surface — how
  `finalise` presents the tracker update it does not run, and which phases read the ticket file. It has
  not yet run on a real project. **Its safety boundaries are NOT Experimental**: local mode is only ever
  declared, never inferred from a missing key; doctor still fails on a missing `tracker`, an unknown
  `mode`, or a missing `tickets_dir`; and in local mode mango runs no tracker command at all.

- **the standalone challenger (`/mango:challenge`).** Running the existing `challenger` once on a raw
  ticket and a diff, outside the lifecycle, is new; what is Experimental is the entry surface — how the
  ticket and the default range are resolved. It has not yet run on a real project. **Its safety
  boundaries are NOT Experimental**: it dispatches the one shipped `challenger` brief unmodified, its
  payload is the raw ticket and the range and nothing else (never a PR body or a working doc), it
  writes nothing, and its output is labelled advisory and never satisfies a review criterion or a gate.

Everything else on the ticket and epic paths is **Stable** — ticket-path classification (want-decision /
how-decision), `ASSUMED` handling, the 1-dispatch exposure-checker, epic detection, the enumerated
six-letter INVEST self-check, and the design blast-radius trace-to-real-producers.

When an Experimental behaviour **graduates**, the CHANGELOG records it explicitly, e.g.
`re-ratification: Experimental → Stable`.
