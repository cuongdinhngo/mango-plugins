## Descriptive vs normative — observe, facilitate, never author

> **mango generates the descriptive and facilitates the normative, but never authors the normative.**

A **descriptive** artifact is a *fact* about what the code or schema **is** — regenerable and
falsifiable (a code sitemap, a database schema map). mango may generate these freely; they are
opt-in, stack-specific adapters (`sitemap`, `db-map`), never core to the lifecycle and never on by
default.

A **normative** artifact is a *rule* — what the code **should** do (the engineering rule book,
database conventions). mango may **facilitate** defining these by **counting the observed patterns
and asking the human to choose** (the `codify` skill), but it must:
- **NEVER author a rule itself**, and never pick, recommend, or default to the majority. Presenting
  "pattern A: 12 files, B: 5" is **data**; concluding "so A is the rule" is **authoring — forbidden**.
- **Never treat "what the code does" as "what the rule should be."** Consistency observed is not
  consent given.
- Tag every recorded standard **`PROVISIONAL (awaiting ratification)`** and keep it provisional until
  a human **explicitly ratifies** it. A provisional draft is a draft for the team — not one person's
  preference frozen as law.

Enforced at `codify` (the counted report + the per-dimension human choice + the ratification gate)
and guarded by `scripts/validate.py` (the boundary tokens). The descriptive adapters change no source
and no schema.
