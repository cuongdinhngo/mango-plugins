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

## The lifecycle

Run the whole thing with `/mango:solve`, or invoke a phase directly. mango **stops and waits at
every ✋ gate** — silence is never approval.

| Skill | Phase / Gate | Produces |
|-------|--------------|----------|
| `/mango:analysis` | 1 → Gate 1 | Requirements matrix (C/R/G/AC) + count line, AC validation, clarification tally, universal inventory, root-cause/gap, blast radius, scope. |
| `/mango:design` | 2 → Gate 2 | Approach + rejected alternatives, smallest change-list traced to rows, rule compliance, the named proving test, rollback + porting. |
| `/mango:execute` | 3 (autonomous) | Branch, the approved change list only, the proving test, a verification sweep (diff ⊆ approved list), commits with no AI co-author trailer. |
| `/mango:review` | 4 (stop if not clean) | `reviewer` + ticket-blind `challenger`, scope reconciliation, regression check, proving-test result, `k/N` coverage. |
| `/mango:finalise` | 5 → final gate | PR draft, per-action approval for every outward action, tracker writes via CLI, follow-up tickets for deferred rows. |
| `/mango:solve` | orchestrator | Runs all phases in order, holding every gate; resumes from `Session status`. |

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
  `branch_strategy` (default `fix|feat|chore/<KEY>-<slug>`), `lessons_path`, `pr_host`,
  `cause_taxonomy`.

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
