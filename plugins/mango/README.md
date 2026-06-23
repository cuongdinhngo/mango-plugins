# mango

A portable, **gated ticket-lifecycle harness** for Claude Code. mango ships the *machinery* — six
gated phases, three read-only review agents, and a working-doc template — and reads every
project-specific rule at runtime from a per-project `.harness.json`. The same plugin installs into
any project unchanged.

**Harness, not rules.** No stack assumptions are baked in (no framework, language, database, or
region specifics). Your engineering rule book, repos, test command, tracker, and ticket schema all
live in `.harness.json`. Trust comes from emitted, counted, gate-blocking artifacts — not prose.

**Secrets never ship.** No token or credential belongs in `.harness.json` or any plugin file; keep
them in a gitignored `.env`.

## Getting set up

| Skill | Use | Produces |
|-------|-----|----------|
| `/mango:init` | Once per project | Detects the stack read-only, interviews only for the undetectable, writes `.harness.json` (guesses marked `UNVERIFIED`), and scaffolds a single-file starter rule book if none exists. |
| `/mango:doctor` | Anytime / before a run | A ✅/⚠/❌ health check of `.harness.json` with exact remediation, prefaced by `mango <version> @ <base path>` so the running version is always visible. `solve` runs it as a fail-fast preflight. |
| `/mango:codify` | When the rule book is missing / thin / inconsistent (opt-in) | **Counts** the conventions the code and schema actually use (code rules **and** database conventions), asks **you** to choose each going-forward standard, and writes them to the rule book tagged **`PROVISIONAL (awaiting ratification)`**. Facilitates; never authors a rule, never auto-picks the majority, never changes code. `doctor` suggests it when the rule book looks thin. |
| `/mango:version-check` | On demand (opt-in) | Reports the running version vs the latest published version and, if newer, **prints** the host `/plugin` commands to update. Needs `update_check_url`; never updates or installs. |

**Defining the rule book — `mango generates the descriptive and facilitates the normative, but never
authors the normative.**` `init` gives you a skeleton rule book with TODOs; when a project has no
rule book, a thin one, or genuinely inconsistent conventions, `/mango:codify` is the deep, opt-in
facilitation. It observes and counts the patterns (presenting "pattern A: 12 files, B: 5" as **data**,
not a verdict), asks you to pick each standard, and records the choices as **provisional** until you
ratify them — the rule the whole plugin grounds in stays the team's decision, never mango's.

### Descriptive maps (opt-in, stack-specific)

Two opt-in adapters generate **descriptive facts** (regenerable, falsifiable) — never normative rules.
They are off unless configured and are **not** part of the lifecycle; the lifecycle runs fully whether
or not either has ever been generated.

| Skill | Use | Produces | Needs |
|-------|-----|----------|-------|
| `/mango:sitemap` | Map the code surface | Routes/endpoints + modules written to `docs_dir` | `code_map_cmd` (or a stack adapter) + `docs_dir` |
| `/mango:db-map` | Map the database schema | Tables, columns+types, primary/foreign keys, indexes, relationships, views/procedures, to `docs_dir` | `db_kind` + (`db_introspect_cmd` **or** `migrations_path`) + `docs_dir` |

A generated `db-map`, **if present**, lets `analysis` widen the Phase-1 blast radius to schema
dependents (columns, FKs, dependent views/procs) — used if present, never required. The *normative*
database conventions live in the `codify` rule book, not in these maps.

## The lifecycle

Run the whole thing with `/mango:solve`, or invoke a phase directly. mango **stops and waits at
every ✋ gate** — silence is never approval.

### Tiers — right-sizing the rigor

`analysis` declares `TIER: lite | full`. **Lite** is chosen only when ALL hold: `SCOPE=S`, a single
file / single requirement row, no universal requirement **with N > 1**, and the ticket is not
security-tagged — otherwise **full**. The lite/full decision keys on the **resolved inventory
denominator N**, not on keywords: a requirement that *sounds* universal ("all/every/no") but resolves
to a single site (**N = 1**) is lite-eligible. Lite routes through `/mango:quick`: two human gates (a
single combined pre-code gate + the final gate), reviewer-only, no challenger, no full matrix, no
fan-out. Full keeps the complete five-phase flow. You can force the lite lane with `/mango:quick
<KEY>`, but `quick` runs a **hard entry check** first and **refuses** (routing you to `/mango:solve`)
if the ticket is security-tagged, touches more than one file, or has a universal requirement that
resolves to N > 1.

| Skill | Phase / Gate | Produces |
|-------|--------------|----------|
| `/mango:analysis` | 1 → Gate 1 | Requirements matrix (C/R/G/AC) + count line, AC validation, clarification tally, universal inventory, root-cause/gap, blast radius, scope. |
| `/mango:design` | 2 → Gate 2 | Approach + rejected alternatives, **Assumptions** (`verified \| novel-untested` — a novel 3p/runtime assumption needs a spike or integration-shaped proof), smallest change-list traced to rows, rule compliance, the named proving test, a **per-AC verification plan** (proof at the layer where the requirement can fail; an `❌` must be upgraded or recorded as a human-approved **coverage-gap exclusion**), rollback + porting. |
| `/mango:execute` | 3 (autonomous) | Branch, the approved change list only, the proving test, a verification sweep (diff ⊆ approved list), commits with no AI co-author trailer. STOPs to **re-gate if the design is invalidated** and via a **stuck-detector** (`stuck_threshold` failed attempts at the same signature). |
| `/mango:review` | 4 (stop if not clean) | `reviewer` + ticket-blind `challenger` (payload excludes the working-doc portion), scope reconciliation, regression check, proving-test result, `k/N` coverage. A challenger "not met" matching a recorded coverage-gap exclusion does not block; an unrecorded gap does. |
| `/mango:finalise` | 5 → final gate | Optional **project finalise-checklist** walk (`pr_checklist_path`), PR draft, per-action approval for every outward action, tracker writes via CLI, follow-up tickets for deferred rows, and a **durable lesson** captured to `lessons_path` on every run. |
| `/mango:quick` | lite lane | Single combined pre-code gate → execute → reviewer-only check → final gate, for trivial tickets. |
| `/mango:solve` | orchestrator | Doctor preflight, then runs all phases in order honouring `TIER`, holding every gate; resumes from `Session status`. |

The four binding principles are in [`PRINCIPLES.md`](./PRINCIPLES.md): think before coding,
simplicity first, surgical changes, goal-driven execution — plus the boundary that **mango generates
the descriptive and facilitates the normative, but never authors the normative.**

## Agents

All review agents are **read-only** — they produce verdicts and findings, never edits.

| Agent | Role | Model |
|-------|------|-------|
| `reviewer` | Rule-book / standards verdict on the diff (BLOCK / CHANGES REQUESTED / LGTM) | Sonnet |
| `reviewer-max` | Same role/rules/output as `reviewer`, for high-stakes diffs under `cost_tier: max` | Opus |
| `challenger` | Ticket-blind requirement reconstruction (met / not met / can't tell, with `path:line`) | Sonnet |
| `onboarder` | Wayfinding / orientation in an unfamiliar codebase | Sonnet |
| `extractor` | Bulk read-and-extract across many files (gathers context; never concludes) | Haiku |

## `.harness.json` config keys

Copy [`config/harness.example.json`](./config/harness.example.json) to your repo root as
`.harness.json`.

**Required**
- `rulebook_path` — your engineering rule book; every phase grounds its rules here.
- `repos` — array of `{name, root}` (supports multi-repo porting).
- `test_command` — the command phases use to run the proving test.
- `tracker` — `{base_url, project_key, cli, read_mcp, fields}`. **Writes go through `cli`; reads may
  use the optional read-only `read_mcp`.** Optional `fields` lists the field set to request on a read
  so one read returns the full ticket (default: description/body, type, labels, parent, priority).
- `ticket_header_schema` — maps each ticket header to `C` / `R` / `G` / `AC`.

**Optional / defaulted**
- `standards_path`, `tickets_dir` (default `docs/tickets`),
  `work_dir` (default = `tickets_dir`; holds the working doc `<KEY>.work.md` when it is a separate
  file), `work_doc_mode` (`auto|separate|embed`, default `auto`; embeds the working doc below a
  raw-ticket separator line when the ticket is itself a local repo file, else a separate file),
  `pr_checklist_path` (optional; a project-owned finalise checklist `finalise` walks before drafting
  the PR), `stuck_threshold` (default `3`; circuit-breaker for repeated failures at the same
  proving artifact), `branch_strategy` (default `fix|feat|chore/<KEY>-<slug>`), `lessons_path`,
  `pr_host`, `cause_taxonomy`, `explore_fanout` (default `true`), `cost_tier`
  (`economy|standard|max`, default `standard`).
- `update_check_url` (optional; raw URL to the published marketplace manifest — lets
  `/mango:version-check` compare running vs latest and print the host update commands. Unset → no
  network call).
- **Descriptive-adapter keys (all optional, off by default):** `docs_dir` (where `sitemap`/`db-map`
  write their regenerable maps), `code_map_cmd` (drives `/mango:sitemap`), and the `db-map` trio —
  `db_kind` plus either `db_introspect_cmd` (read-only schema introspection) or `migrations_path`
  (derive the schema from migration files). With these unset, the adapters report they are not
  configured and do nothing.

`rulebook_path` may be a **file or a directory**; with a directory, every consumer reads all `*.md`
inside it. Run `/mango:init` to generate this file for you.

## Operational notes

- **Plugin administration belongs to the host.** Installing, reinstalling, pinning a version, or
  reordering the install registry is done **from the host** with `/plugin` — never from a restricted
  or remote channel where `/plugin` is unavailable. mango **detects and informs; it never
  self-administers.**
- **If you find yourself working around the loader/registry from a restricted channel — stop and do
  it from the host.** mango will not install, reinstall, reorder a registry, or run `/plugin` for you.
- **Verify the live version from `doctor`'s first line**, not by assuming. `/mango:doctor` prints
  `mango <version> @ <base path>` as line 1 — a green doctor does **not** prove the version you
  intended is the one actually loaded; a stale version can run silently behind a passing preflight.
- **Use `/mango:version-check`** (if `update_check_url` is configured) to learn whether a newer
  version has been published. It reports running vs latest and **prints** the host `/plugin` commands
  to update — it does not update anything.

## Cost profile

The full tier is heavier — rule-book reads, requirement re-derivation, the challenger, and (when
`explore_fanout` is `true`) read-only Explore fan-out during investigation. For small, low-stakes,
high-volume tickets use the **lite** tier (`/mango:quick`), which skips fan-out and the challenger.
Set `explore_fanout: false` to disable investigation fan-out on the full tier too.

### Model delegation

mango routes by the **nature of the task**, not the phase: *Opus decides, Sonnet executes, Haiku
gathers — and every decision or verdict is produced or ratified by the strong model; a weaker model
may only gather, never conclude.*

| Step | Model |
|------|-------|
| Orchestrator + gates, analysis judgment, design | Opus (the model you drive) |
| Review verdict + challenger reconstruction (highest judgment) | Sonnet — the `reviewer-max` agent (Opus) for high-stakes diffs under `cost_tier: max` — **never Haiku** |
| Implement the approved change list; draft PR body; Explore | Sonnet |
| Bulk read-and-extract across many files (`agents/extractor.md`) | Haiku |
| grep stray refs / run tests / lint | no model — Bash directly |

`cost_tier` shifts the dials **within** this map, never against it: `economy` pushes more bulk
retrieval to the Haiku `extractor` and avoids Opus on review; `standard` is the map above; `max`
dispatches the **`reviewer-max`** agent (Opus) for high-stakes diffs (security-tagged, or touching
auth / data access / schema migration). Since a skill cannot re-pin a subagent's model at runtime,
the Opus upgrade is a **choice of agent** (`reviewer-max` vs `reviewer`), which `review` selects
explicitly — not a runtime setting. `reviewer`/`reviewer-max`/`challenger` are never Haiku, and the
lite tier runs on a single model. The full routing map lives in [`PRINCIPLES.md`](./PRINCIPLES.md).

## Testing the harness itself

`scripts/validate.py` is the cheap, always-on guard — structural checks plus per-skill contract
tokens (it fails if a skill loses its load-bearing artifact). `tests/eval/` is the real behavioural
check: `run.sh` drives `claude -p` over fixture tickets and asserts the expected artifacts. Beyond
the analysis happy path (count line, gate count, freeform Gate-0 confirmation) it also exercises the
behaviours that matter most — proof at the risk layer (`design` flags a unit proof for an
integration-layer AC), the ticket-blind `challenger` catching an unmet AC, the design-invalidated
escalation, and the stuck-detector. It costs tokens, so CI runs it only via the manual `eval.yml`
workflow (`workflow_dispatch`, needs the `ANTHROPIC_API_KEY` secret).

## First run

```
# 1. install (see the marketplace README)
# 2. in your project:
cp <plugin>/config/harness.example.json .harness.json
#    edit .harness.json — rulebook_path, repos, test_command, tracker, ticket_header_schema
# 3. start a ticket:
/mango:solve PROJ-123
```

If `.harness.json` is missing, every skill stops and tells you to create one from the example.
