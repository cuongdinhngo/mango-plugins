## Maturity — Stable vs Experimental

Every shipped behaviour carries an honest maturity level so a reader knows what is settled:

- **Stable** — committed behaviour, field-tested, safe to rely on. This is the default for everything
  not marked otherwise.
- **Experimental** — works and has been validated, but its exact shape may still change until further
  real-world use. Marked explicitly at the behaviour.

Two behaviours are **Experimental** today:

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
