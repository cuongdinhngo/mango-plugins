# mango-plugins

![version](https://img.shields.io/badge/version-1.23.0-blue)
![license](https://img.shields.io/badge/license-MIT-green)
[![validate](https://github.com/cuongdinhngo/mango-plugins/actions/workflows/validate.yml/badge.svg)](https://github.com/cuongdinhngo/mango-plugins/actions/workflows/validate.yml)

**mango** is the verification layer for AI-assisted delivery in Claude Code; this repo is the
**marketplace** that hosts it ([`plugins/mango`](./plugins/mango)). Your agent does the work. mango
checks it against the ticket, holds the gates you approve, binds every piece of evidence to a commit,
and says plainly what it could not verify.

Protocol v0.1 (Draft) · Conformance: L2 (full lane) — [protocol](./docs/PROTOCOL.md) · [roadmap](./docs/ROADMAP.md)

> **Review evidence, not confidence.**

## Why mango?

AI coding agents write code well and judge "done" badly: an acceptance criterion skipped, a test that
proves the wrong thing, an edge case never considered, a hidden assumption left in. mango routes every
ticket through **gated phases** that each produce **checkable artifacts**. You approve a diff on
evidence, not vibes. Silence is never approval.

- ✅ A **requirements matrix** with explicit counts — nothing slips through unnamed
- ✅ A **proving test at the right layer** — a runtime requirement can't be closed by a unit-mock proof
- ✅ An independent **challenger** that never sees the work — it flags what the diff leaves unmet
- ✅ **Human approval gates** before every important transition
- ✅ A **PR + tracker update + durable lesson**, each behind explicit per-action approval

## Try it in 2 minutes

```
/plugin marketplace add cuongdinhngo/mango-plugins
/plugin install mango@mango-plugins
/mango:challenge path/to/ticket.md main..your-branch
```

No setup, nothing written: the ticket-blind challenger rebuilds the requirements from the ticket alone
and marks each met / not met / can't tell, with a `path:line`. Advisory only; the gated workflow (*Quick
start*) adds the [counted matrix](./docs/concepts/lifecycle.md#what-the-artifacts-look-like). The shape:

```
1. AC-3  password reset invalidates the old token   met        src/auth/reset.ts:88
2. R-5   audit log entry written on failure         met        src/audit/log.ts:22
3. AC-4  rate limit applies to the reset endpoint   not met    —

14 requirements: 13 met, 1 not met, 0 can't tell
```

## Quick start

Needs git, Python 3.7+, a test command, and a tracker or local mode ([prerequisites](./docs/howto/set-up-a-project.md#prerequisites)):

```
/mango:init          # detect your stack, write .harness.json, scaffold a starter rule book
/mango:doctor        # health-check the setup (✅/⚠/❌ with remediation)
/mango:solve PROJ-123
```

`init` marks every inferred value `UNVERIFIED` and writes **no secrets**. By hand: copy
`<plugin>/config/harness.minimal.json` to `.harness.json`, replace each `REPLACE_ME`, create `tickets_dir`,
and create the rule book file at `rulebook_path` — empty is fine (`doctor` warns it is a stub). Other keys
are in `harness.example.json`. No rule book? [`/mango:codify`](./docs/howto/set-up-a-project.md)
counts your conventions and asks **you** to choose. Team rollout: [`docs/ADOPTION.md`](./docs/ADOPTION.md).

## The lifecycle

Six phases per ticket. You approve at Gate 1 (analysis), Gate 2 (design) and each outward action, plus
a **Gate 0** for an ambiguous ticket. Execute flows into review, which stops only when the work is not clean.

| Phase | What it does |
|-------|--------------|
| **0 · refine** | Exposes the ticket's unresolved product decisions — resolves the *how* ones with a citation, asks you the *want* ones — then self-skips when the ticket is already clear. Never authors your intent. |
| **1 · analysis** | Decomposes every section into a counted requirements matrix, records a `BASELINE` for the existing test state, and gathers the Phase-1 evidence behind each row. |
| **2 · design** | The approach, the rejected alternatives, the smallest change-list traced to matrix rows, and a per-requirement verification plan whose layer-match — and, for an AC whose answer depends on the shape of real input, whose **fixture provenance** — is a hard gate. |
| **3 · execute** | Only the approved changes, on one branch, with the proving test — committed *before* review is dispatched. |
| **4 · review** | An independent, ticket-blind **challenger** rebuilds the requirements and judges the diff against them. |
| **5 · finalise** | PR draft, tracker update, and a durable lesson — one explicit approval per outward action. |

**Epics** take the epic path: `breakdown` into tickets, approved by you before any executes. **Run it:**
`/mango:solve <KEY>`, any phase directly, or `/mango:quick <KEY>` for the lite lane; unattended with
`/mango:autorun` — no gate removed, no auto-merge ([details](./docs/concepts/unattended-runs.md)).
Beyond the lifecycle: `init` · `doctor` · `codify` · `promote` · `version-check` · `budget`, the one-shot
`challenge`, and opt-in maps `sitemap` and `db-map` — the [plugin README](./plugins/mango/README.md) has what each produces.

## With your host's commands

mango does not replace `/plan`, `/code-review`, `/security-review`, `/verify` or `/run`: use them to do
the work, and mango checks the result against the ticket. Recording their output as mango evidence is
**Planned** ([protocol §7](./docs/PROTOCOL.md#7-evidence-from-other-tools-and-conformance)).

## Maturity

**Every release is gated by `validate.py` and the dispatch-free script suites**, run in CI on every
push. **mango has no behavioural regression suite.** It has a per-skill smoke guard of 8 fixtures, run
when a skill is edited, which does **not** detect cross-skill regressions, and a weekly
[golden e2e](./tests/e2e/) of one ticket through `autorun`, which catches one only when it breaks that
run. `RETIRE:` is uncovered. [Experimental](./plugins/mango/principles/maturity.md) · [detail](./docs/MATURITY.md) · [cost](./docs/COST.md).

## Update and pin

Every push to `main` ships; every version bump is tagged `v<version>` with a
[GitHub Release](https://github.com/cuongdinhngo/mango-plugins/releases) (from `v1.18.2`). Policy: [`docs/STABILITY.md`](./docs/STABILITY.md).

```
/plugin marketplace update mango-plugins                    # update to the latest
/plugin install mango@mango-plugins
/plugin marketplace add cuongdinhngo/mango-plugins#v1.23.0  # or pin a tag (current shown; any works)
```

## Contributing and license

[CONTRIBUTING.md](./CONTRIBUTING.md) — read *Skills are directive-only* before editing a skill. MIT — [LICENSE](./LICENSE).
