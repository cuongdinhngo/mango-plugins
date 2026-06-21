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
| `/mango:doctor` | Anytime / before a run | A ✅/⚠/❌ health check of `.harness.json` with exact remediation. `solve` runs it as a fail-fast preflight. |

## The lifecycle

Run the whole thing with `/mango:solve`, or invoke a phase directly. mango **stops and waits at
every ✋ gate** — silence is never approval.

### Tiers — right-sizing the rigor

`analysis` declares `TIER: lite | full`. **Lite** is chosen only when ALL hold: `SCOPE=S`, a single
file / single requirement row, no universal ("all/every/no") requirement, and the ticket is not
security-tagged — otherwise **full**. Lite routes through `/mango:quick`: two human gates (a single
combined pre-code gate + the final gate), reviewer-only, no challenger, no full matrix, no fan-out.
Full keeps the complete five-phase flow. Force the lite lane with `/mango:quick <KEY>`.

| Skill | Phase / Gate | Produces |
|-------|--------------|----------|
| `/mango:analysis` | 1 → Gate 1 | Requirements matrix (C/R/G/AC) + count line, AC validation, clarification tally, universal inventory, root-cause/gap, blast radius, scope. |
| `/mango:design` | 2 → Gate 2 | Approach + rejected alternatives, **Assumptions** (`verified \| novel-untested` — a novel 3p/runtime assumption needs a spike or integration-shaped proof), smallest change-list traced to rows, rule compliance, the named proving test, a **per-AC verification plan** (proof at the layer where the requirement can fail — no `❌`), rollback + porting. |
| `/mango:execute` | 3 (autonomous) | Branch, the approved change list only, the proving test, a verification sweep (diff ⊆ approved list), commits with no AI co-author trailer. STOPs to **re-gate if the design is invalidated** and via a **stuck-detector** (`stuck_threshold` failed attempts at the same signature). |
| `/mango:review` | 4 (stop if not clean) | `reviewer` + ticket-blind `challenger` (payload excludes the `.work.md`), scope reconciliation, regression check, proving-test result, `k/N` coverage. |
| `/mango:finalise` | 5 → final gate | PR draft, per-action approval for every outward action, tracker writes via CLI, follow-up tickets for deferred rows, and a **durable lesson** captured to `lessons_path` on every run. |
| `/mango:quick` | lite lane | Single combined pre-code gate → execute → reviewer-only check → final gate, for trivial tickets. |
| `/mango:solve` | orchestrator | Doctor preflight, then runs all phases in order honouring `TIER`, holding every gate; resumes from `Session status`. |

The four binding principles are in [`PRINCIPLES.md`](./PRINCIPLES.md): think before coding,
simplicity first, surgical changes, goal-driven execution.

## `.harness.json` config keys

Copy [`config/harness.example.json`](./config/harness.example.json) to your repo root as
`.harness.json`.

**Required**
- `rulebook_path` — your engineering rule book; every phase grounds its rules here.
- `repos` — array of `{name, root}` (supports multi-repo porting).
- `test_command` — the command phases use to run the proving test.
- `tracker` — `{base_url, project_key, cli, read_mcp}`. **Writes go through `cli`; reads may use the
  optional read-only `read_mcp`.**
- `ticket_header_schema` — maps each ticket header to `C` / `R` / `G` / `AC`.

**Optional / defaulted**
- `standards_path`, `tickets_dir` (default `docs/tickets`),
  `work_dir` (default = `tickets_dir`; holds the working doc `<KEY>.work.md`, kept separate from the
  ticket spec), `stuck_threshold` (default `3`; circuit-breaker for repeated failures at the same
  proving artifact), `branch_strategy` (default `fix|feat|chore/<KEY>-<slug>`), `lessons_path`,
  `pr_host`, `cause_taxonomy`, `explore_fanout` (default `true`), `cost_tier`
  (`economy|standard|max`, default `standard`).

`rulebook_path` may be a **file or a directory**; with a directory, every consumer reads all `*.md`
inside it. Run `/mango:init` to generate this file for you.

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
| Review verdict + challenger reconstruction (highest judgment) | Sonnet — Opus for high-stakes diffs — **never Haiku** |
| Implement the approved change list; draft PR body; Explore | Sonnet |
| Bulk read-and-extract across many files (`agents/extractor.md`) | Haiku |
| grep stray refs / run tests / lint | no model — Bash directly |

`cost_tier` shifts the dials **within** this map, never against it: `economy` pushes more bulk
retrieval to the Haiku `extractor` and avoids Opus on review; `standard` is the map above; `max`
allows Opus on review for high-stakes work. `reviewer`/`challenger` are never demoted to Haiku, and
the lite tier runs on a single model. The full routing map lives in
[`PRINCIPLES.md`](./PRINCIPLES.md).

## Testing the harness itself

`scripts/validate.py` is the cheap, always-on guard — structural checks plus per-skill contract
tokens (it fails if a skill loses its load-bearing artifact). `tests/eval/` is the real behavioural
check: `run.sh` drives `claude -p` over fixture tickets and asserts the expected artifacts (count
line, gate count, the freeform Gate-0 confirmation). It costs tokens, so CI runs it only via the
manual `eval.yml` workflow (`workflow_dispatch`, needs the `ANTHROPIC_API_KEY` secret).

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
