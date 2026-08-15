---
name: codify
description: Facilitated, opt-in way to define a project's engineering rule book and database conventions when it is missing, thin, or inconsistent. Observes and COUNTS the patterns the code/schema actually use, asks the human to choose each going-forward standard, and records the choices as a PROVISIONAL rule book awaiting ratification. It never authors a rule, never auto-picks the majority, and never changes code.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md` — and especially its **observe / facilitate /
never-author** boundary. `codify` helps a team *define* the standard; it does **not invent** one.

**READ `<mango>/principles/descriptive-normative.md` NOW, before counting anything.** It is the binding
observe/facilitate/never-author contract. Unconditional, not consult-if-relevant. If `<mango>` does not
resolve, say so and hold the boundary restated below.

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
   written to `config.drift_path` when set — but **never change code**. That same list is where a
   type-6 **adjudicated non-defect** lands (a deviation examined and accepted), each such entry carrying
   its **`expiry:` condition** so an accepted deviation is never a permanent exemption nobody chose.

   **The drift count is a COUNTED LINE, not prose.** Whenever you emit or update the drift list, emit
   the count as a prefixed counting line — the same shape as `REFINE:` / `BREAKDOWN:` / `SECTIONS:`,
   which is what makes a count resist fudging:

   `DRIFT: <n> entries | <m> tickets`

   `<n>` is the number of drift entries recorded; `<m>` is the number of follow-up tickets they roll up
   into. Both are **counted from the list itself**, never narrated from memory — a prose count ("about
   six files drift") is exactly what lets a "6" ship where the list holds 5.
3a. **Uncodified-standard items surfaced by the lifecycle.** A lifecycle phase (e.g. `analysis`) may
   surface an **uncodified standard** — a standard applied at a gate with **no codified rule** in the
   rule book. Such an item enters this **same provisional→ratify flow**: record it as a
   `PROVISIONAL (awaiting ratification)` entry for the human to ratify, presenting *how* it was being
   applied as **data**, never auto-authoring the rule from that observed usage. It stays provisional —
   and cannot silently gate-block as if codified — until the human ratifies it.
3b. **A promoted CLAIM from the learning loop enters this SAME provisional→ratify flow.** `finalise`'s
   learning loop may propose a claim for promotion into the rule book (a type-2 code heuristic, a
   type-5-normative project fact) **after** it has passed recurrence **and** the falsification check —
   see `<mango>/PRINCIPLES.md` (The learning loop). Record it here exactly as any other
   provisional entry: write it into `config.rulebook_path` tagged
   `PROVISIONAL (awaiting ratification)`, carrying its **claim ID + evidence** so the rule is traceable
   to what produced it, and an **ID + blocking status** when the claim was type-5-normative. Three
   constraints hold, and each is checkable:
   - **The rule goes in the rule book, never into `CLAUDE.md`** — nor into whichever always-on context
     file the host loads (`config.context_file`, which may be `AGENTS.md`). That file carries only the
     pointer `init` wrote. Create the rule book at `config.rulebook_path` if it is absent. The promotion
     is not done until the rule is in the rule book **and** `doctor` is green on the context-file →
     rule-book pointer — `init`/`doctor` own that wiring already, including resolving which file the
     host actually loads; reuse it.
   - **A PROCESS claim never lands in the code rule book** — it goes to `config.agent_brief_path` (a
     PROJECT file, never one of mango's own agent briefs). Route by subject, not by convenience.
   - **Nothing here edits a mango file.** A type-3 skill-gap claim is **not** a rule-book candidate at
     all: it is a signal recorded in `config.skill_gap_path` for mango's maintainer.
4. **Ratification gate (✋).** Nothing becomes a binding rule until the human **explicitly ratifies**
   the set. State plainly that this is a **draft for the team**, not one person's preference frozen as
   law. On ratify, remove the `PROVISIONAL (awaiting ratification)` tags; until then they stay.
5. **Boundary self-check.** Confirm before finishing: no code was changed; no standard was
   auto-picked, recommended, or defaulted to the majority; every recorded entry is tagged PROVISIONAL
   and stays provisional until human ratification; every promoted claim landed in a **PROJECT** file
   (the rule in `config.rulebook_path`, a process claim in `config.agent_brief_path`, never a copy in
   `CLAUDE.md`) and **no mango file was written**.
