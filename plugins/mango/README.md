# mango

A portable, **gated ticket-lifecycle harness** for Claude Code. mango ships the *machinery* — a Phase-0
`refine` phase, five gated lifecycle phases, read-only review agents, and a working-doc template — and
reads every project-specific rule at runtime from a per-project `.harness.json`. The same plugin
installs into any project unchanged.

**Harness, not rules.** No stack assumptions are baked in (no framework, language, database, or
region). Your rule book, repos, test command, tracker, and ticket schema all live in `.harness.json`.
Trust comes from emitted, counted, gate-blocking artifacts — not prose. mango generates the
descriptive and facilitates the normative, but **never authors the normative** — the rules stay your
team's decision. No secrets ship: tokens live only in a gitignored `.env`.

**mango is not install-and-go.** Installing the plugin gives you the machinery and no rules. Before the
first ticket, set the project up: [Set up a project](../../docs/howto/set-up-a-project.md). Until
`.harness.json` exists, every skill stops and tells you to create one.

## Quickstart

```
# 1. install (see the marketplace README)
# 2. in your project:
/mango:init          # or copy config/harness.minimal.json to .harness.json and fill it in
/mango:doctor
# 3. start a ticket:
/mango:solve PROJ-123
```

By hand: copy `config/harness.minimal.json` to `.harness.json`, replace each `REPLACE_ME`, create
`tickets_dir`, and create the rule book file at `rulebook_path` — an empty file is enough to start
(`doctor` warns it is a stub; it does not fail). Every key: [config reference](../../docs/reference/config.md).

## Skills

| Skill | Role | What it does |
|---|---|---|
| `/mango:refine` | phase 0 | Exposes the ticket's unresolved decisions; resolves the *how* with a citation, asks you the *want*. |
| `/mango:analysis` | phase 1 → Gate 1 | Counted requirements matrix (C/R/G/AC), root cause, blast radius, `BASELINE`. |
| `/mango:design` | phase 2 → Gate 2 | Approach, rejected alternatives, smallest row-traced change list, the named proving test. |
| `/mango:execute` | phase 3 | Only the approved changes plus the proving test, committed before review. |
| `/mango:review` | phase 4 | Reviewer plus ticket-blind challenger; stops only when the work is not clean. |
| `/mango:finalise` | phase 5 → final gate | PR, tracker update and durable lesson, one approval per outward action. |
| `/mango:solve` | orchestrator | Runs the phases in order, holding every gate; resumes from the working doc. |
| `/mango:quick` | lite lane | One combined pre-code gate, execute, reviewer-only check, final gate. |
| `/mango:autorun` | unattended | Same phases, gates closed on artifacts, stops at the PR; never merges. |
| `/mango:breakdown` | epic path | Splits an epic into tickets with an INVEST self-check, behind a human gate. |
| `/mango:challenge` | one-shot | Runs the ticket-blind challenger once on any branch; advisory, writes nothing. |
| `/mango:spec-review` | spec (pre-ticket) | Fresh read-only reviewers, one per lens, give a spec or design doc a counted verdict; advisory. |
| `/mango:init` | setup | Detects the stack, writes `.harness.json` (guesses marked `UNVERIFIED`). |
| `/mango:doctor` | setup | ✅/⚠/❌ health check with remediation; prints the running version first. |
| `/mango:codify` | rules (opt-in) | Counts conventions in use; **you** choose each standard; recorded provisional. |
| `/mango:promote` | rules (opt-in) | Proposes a project rule from a lesson class seen on ≥ 2 tickets; you ratify. |
| `/mango:sitemap` | map (opt-in) | Descriptive code-surface map into `docs_dir`. |
| `/mango:db-map` | map (opt-in) | Descriptive schema map into `docs_dir`. |
| `/mango:budget` | cost (opt-in) | Detects token optimizers and records your provisional adoption choice. |
| `/mango:version-check` | on demand | Compares running vs latest and prints the host `/plugin` commands; never updates. |

## Agents

All agents except `implementer` are **read-only** — they produce verdicts and findings, never edits.
`implementer` is the one writer: it lands a Gate-2-approved change list on the branch it is given and
returns raw evidence; it never decides.

| Agent | Role | Model |
|-------|------|-------|
| `implementer` | Execute-phase worker: implements ONLY the approved change list + proving test, commits, returns verbatim test output (the main loop implements instead for a high-stakes change) | Sonnet |
| `explorer` | Analysis fan-out: handler / entry point, callers, dependents, blast radius, as `path:line` (gathers; never decides scope or root cause) | Sonnet |
| `reviewer` | Rule-book / standards verdict on the diff (BLOCK / CHANGES REQUESTED / LGTM) | Sonnet |
| `reviewer-max` | Same role, for high-stakes diffs under `cost_tier: max` | Opus |
| `challenger` | Ticket-blind requirement reconstruction (met / not met / can't tell, with `path:line`) | Sonnet |
| `spec-reviewer` | One lens over a spec or design doc; `Read, Grep, Glob` only, no CLAUDE.md at start | Sonnet |
| `onboarder` | Wayfinding / orientation in an unfamiliar codebase | Sonnet |
| `extractor` | Bulk read-and-extract across many files (gathers context; never concludes) | Haiku |

## Learn more

| If you want to… | Read |
|---|---|
| set a project up | [Set up a project](../../docs/howto/set-up-a-project.md) |
| understand the phases, tiers and epic path | [The lifecycle](../../docs/concepts/lifecycle.md) |
| hand a ticket over for the night | [Unattended runs](../../docs/concepts/unattended-runs.md) |
| use the frontend gates | [Frontend track](../../docs/concepts/frontend-track.md) |
| see how lessons come back | [The learning loop](../../docs/concepts/learning-loop.md) |
| know which model does what, and the cost | [Cost and models](../../docs/concepts/cost-and-models.md) |
| look up a config key or a counted line | [config](../../docs/reference/config.md) · [lines](../../docs/reference/lines.md) |
| know what mango guarantees | [Protocol](../../docs/PROTOCOL.md) |

## Maturity

Which behaviours are **Experimental** is recorded in one place: [`principles/maturity.md`](./principles/maturity.md).
Everything else is Stable, and the safety boundaries (no gate removed, no auto-merge, `not-checkable` is
never a pass) are never Experimental. The four binding principles are in [`PRINCIPLES.md`](./PRINCIPLES.md).

## Operational notes

- **Plugin administration belongs to the host.** Installing, reinstalling, pinning a version, or
  reordering the registry is done from the host with `/plugin` — never from a restricted or remote
  channel. mango detects and informs; it never self-administers.
- **Verify the live version from `doctor`'s first line**, not by assuming — a stale version can run
  silently behind a passing preflight. Use `/mango:version-check` (if configured) to learn whether a
  newer version has been published.
- **`.harness.json` commit policy is resolved at `init`**: it asks whether the config is committed
  (shared) or kept local (gitignored). Either way it writes no secrets.

## Contributing

Skills are directive-only: the rule goes in the skill, the reason in [`CHANGELOG.md`](./CHANGELOG.md).
mango's own test tooling lives in the source repository, not in the installed plugin; read
`CONTRIBUTING.md` at [github.com/cuongdinhngo/mango-plugins](https://github.com/cuongdinhngo/mango-plugins).
