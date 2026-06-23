---
name: codify
description: Facilitated, opt-in way to define a project's engineering rule book and database conventions when it is missing, thin, or inconsistent. Observes and COUNTS the patterns the code/schema actually use, asks the human to choose each going-forward standard, and records the choices as a PROVISIONAL rule book awaiting ratification. It never authors a rule, never auto-picks the majority, and never changes code.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` — and especially its **observe / facilitate /
never-author** boundary. This skill exists because the rule book is the single thing the whole plugin
grounds in: when it is absent, thin, or genuinely inconsistent, the reviewer and challenger produce
generic, low-value output. `codify` helps a team *define* the standard; it does **not invent** one.

> **The boundary (binding).** mango may **generate descriptive facts** (what the code/schema *is* —
> regenerable, falsifiable) and may **facilitate defining normative rules** by **counting the
> observed patterns and asking the human to choose**. mango must **NEVER author a normative rule
> itself**, never pick / recommend / default to the majority, and never treat "what the code does" as
> "what the rule should be." Showing "pattern A: 12 files, B: 5" is **data**; saying "so A is the
> rule" is **authoring — forbidden**. Every normative entry is **PROVISIONAL until a human ratifies
> it.**

`codify` is **opt-in and read-only on code**. It writes only the rule-book draft (and, optionally, a
drift list). It is **not** part of the lifecycle. Relationship to the others: `init` stays the light
bootstrap (skeleton rule book with TODOs); `codify` is the deep facilitation; `doctor` only
*suggests* `codify` when the rule book looks missing or thin — it never runs it.

## Steps

1. **Observe + count (read-only).** Scan the codebase, and — only if a DB adapter/config exists
   (`config.db_kind` with `config.db_introspect_cmd` or `config.migrations_path`, via the `db-map`
   skill) — the schema. Produce a **counted inconsistency report**: for each dimension below, list the
   observed patterns with **counts** and example `path:line`. Explicitly flag any dimension with **no
   dominant pattern** as **"no consistent rule found"**. Dimensions (generic):
   - **Code:** error handling, naming / case styles, layering / structure, input validation, logging,
     import / dependency style.
   - **Database conventions:** table / column naming, timestamp convention, soft-delete vs
     hard-delete, foreign-key on-delete policy, raw-SQL vs query-builder / ORM, migration style
     (numbered? reversible? idempotent?).
   Delegate the bulk read-and-extract to the Haiku `extractor` worker per `PRINCIPLES.md`; run
   grep/counts via the Bash tool directly. Counting is judgment-light — but the report is **data
   only**.
2. **Facilitate a decision per dimension.** Present the counted options and **ask the human to
   choose** the going-forward standard for each dimension. Present counts as **observed facts** — you
   may state "the majority is X" as a fact — but **do not pick, recommend, or default to** any option,
   including the majority. The choice is the human's. A dimension flagged "no consistent rule found"
   still requires a human choice (or an explicit "leave undecided").
3. **Record as a PROVISIONAL rule book.** Write each *chosen* standard into `config.rulebook_path`
   (a file, or a directory per the file-or-directory rule) under the appropriate section. Tag every
   entry **`PROVISIONAL (awaiting ratification)`**. Never write a dimension the human did not choose.
   Optionally emit a **drift list** of files diverging from a chosen standard as follow-up tech-debt —
   but **never change code**.
4. **Ratification gate (✋).** Nothing becomes a binding rule until the human **explicitly ratifies**
   the set. State plainly that this is a **draft for the team**, not one person's preference frozen as
   law. On ratify, remove the `PROVISIONAL (awaiting ratification)` tags; until then they stay.
5. **Boundary self-check.** Confirm before finishing: no code was changed; no standard was
   auto-picked, recommended, or defaulted to the majority; every recorded entry is tagged PROVISIONAL
   and stays provisional until human ratification.
