## Maturity — Stable vs Experimental

Every shipped behaviour carries an honest maturity level so a reader knows what is settled:

- **Stable** — committed behaviour, field-tested, safe to rely on. This is the default for everything
  not marked otherwise.
- **Experimental** — works and has been validated, but its exact shape may still change until further
  real-world use. Marked explicitly at the behaviour.

Four behaviours are **Experimental** today:

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

- **breakdown re-ratification** (surfacing a post-gate split delta for an explicit human re-approve):
  validated once in the field, its re-ratification trigger and granularity may change until a second
  epic exercises it.
- **the learning loop's classification and promotion machinery** — where the six-type boundaries fall,
  which recall key each type gets, and how a recurrence is scored. It is built on three probe rounds over
  real lesson files, but its *shape* will move as more lesson files run through it. **Its five invariants
  are NOT Experimental** and never will be: the classifier proposes and the human confirms, recall is
  advisory, falsification precedes ratification, lessons never modify mango, and everything is
  project-local. Those are safety boundaries, not a shape to be tuned.

Everything else on the ticket and epic paths is **Stable** — ticket-path classification (want-decision /
how-decision), `ASSUMED` handling, the 1-dispatch exposure-checker, epic detection, the enumerated
six-letter INVEST self-check, and the design blast-radius trace-to-real-producers.

When an Experimental behaviour **graduates**, the CHANGELOG records it explicitly, e.g.
`re-ratification: Experimental → Stable`.
