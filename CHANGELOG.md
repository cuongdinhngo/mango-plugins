# Changelog

All notable changes to the mango plugin are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

## [0.3.0] — 2026-06-21

Retrospective-driven hardening. Unlike v0.2 (predicted risks), these six fixes come from **two real
mango runs**. Each fix cites the observed failure that motivated it. No v0.2 behaviour was removed.

### Added / Changed
- **A — Proof at the risk layer + per-AC verification plan.** `design` Phase 2 now emits a
  verification-plan table (`AC | risk layer | proof artifact | layer-match? ✅/❌`); the proving test
  must sit at the layer where the requirement can fail, and **Gate 2 may not pass with any ❌**.
  Principle 4 in `PRINCIPLES.md` and the ticket template updated. *(Observed: a store unit test
  passed while the integration-layer feature was broken — Gate 2 cleared on a false green; and an
  "in-browser confirm" verification artifact surfaced only at Gate 4.)*
- **B — Spike novel library/runtime assumptions before Gate 2.** `design` adds an **Assumptions**
  step (`verified | novel-untested`); a `novel-untested` third-party/runtime assumption must be
  resolved by a recorded **spike** or an integration/e2e-shaped proving test before Gate 2.
  *(Observed: a design leaned on the untested "two live rich-text editors coexist" assumption — the
  exact thing that broke.)*
- **C — Execute escalation / re-gate.** `execute` defines a **"design invalidated"** STOP: when a
  test proves the approved approach can't work, execute stops, records the finding, surfaces options,
  and **re-opens Gate 2** (re-passing A + B) — never continues with a known-broken approach. `solve`
  defines the `execute → (design-invalidated) → design re-gate` transition. *(Observed: execute found
  the Gate-2 approach unworkable but mango had no defined transition; the operator improvised.)*
- **D — Stuck-detector / circuit-breaker.** `execute` and `quick` STOP and escalate after `K` failed
  attempts at the same failing-test signature (default `K=3`, configurable `stuck_threshold` in
  `.harness.json`); the counter resets when the signature changes. *(Observed: ~7 attempts against
  the same failing e2e before escalating.)*
- **E — Finalise captures a durable lesson on every run.** `finalise` now asks for a durable lesson
  (constraint / wrong assumption / process gap) **independent of deferred rows** and writes it to
  `config.lessons_path` as a repo artifact, never only personal memory. Reinforced in `PRINCIPLES.md`.
  *(Observed: a durable constraint nearly never reached `LESSONS.md` because there were no deferred
  rows to hang it on.)*
- **F — Working doc separated from the ticket spec.** The working doc moves to
  `<config.work_dir>/<KEY>.work.md` (default `work_dir` = `tickets_dir`), a distinct file never
  appended to the ticket spec; the `challenger` payload provably excludes it. `analysis`, `review`,
  `solve`, the template, `PRINCIPLES.md`, and `challenger.md` updated — independence is now backed by
  a path separation (still procedural, not cryptographic). *(Observed: the ticket file doubled as the
  working doc, so challenger independence was a convention, not structure.)*
- **Validator.** `scripts/validate.py` skill-contract checks now require `risk layer` + `Assumptions`
  in `design`, a stuck/escalation token + a "design invalidated" token in `execute`, and
  `durable lesson` in `finalise`.

## [0.2.0] — 2026-06-20

Architecture-review hardening. Each item closes a specific adoption risk; no full-tier v1 behaviour
was removed.

### Added
- **IMP-1 `/mango:init`** — bootstraps `.harness.json` (detect stack read-only, interview only for
  the undetectable, mark guesses `UNVERIFIED`) and scaffolds a single-file starter rule book
  (`skills/init/rulebook-template.md`) when none exists. `rulebook_path` may now be a **file or a
  directory** (reviewer/onboarder read all `*.md` in a directory).
- **IMP-2 `/mango:doctor`** — health-checks `.harness.json` with a ✅/⚠/❌ checklist and exact
  remediation; `solve` gains a fail-fast preflight that refuses to start while any ❌ remains.
- **IMP-3 Right-sizing** — `analysis` declares `TIER: lite | full`; new `/mango:quick` lite lane
  (two human gates, reviewer-only, no challenger/matrix/fan-out); `solve` routes by tier.
- **IMP-4 Freeform tickets** — `analysis` synthesizes the matrix, sets `STRUCTURE: synthesized`, and
  forces a Gate-0 confirmation of the reading.
- **IMP-5 Behavioural guard** — `validate.py` adds per-skill contract token checks; optional
  `tests/eval/` harness (`run.sh` + fixtures) and a manual `eval.yml` workflow.
- **IMP-6 Honest independence** — `review` builds the challenger's input explicitly (re-fetched raw
  ticket + diff only); `challenger.md`/`PRINCIPLES.md` state the independence is procedural.
- **IMP-7 Cost knob** — `explore_fanout` config key (default `true`); lite tier always skips
  fan-out; README cost-profile note.
- **IMP-8 Model delegation** — routing map + the "Opus decides, Sonnet executes, Haiku gathers"
  principle in `PRINCIPLES.md`; `cost_tier` config key (`economy|standard|max`, default `standard`);
  a Haiku-pinned read-only `agents/extractor.md` for bulk read-and-extract; `analysis`/`execute`/
  `review` honour `cost_tier` and run shell directly (no model). `reviewer`/`challenger` stay on
  Sonnet (upgradable to Opus, never Haiku); lite tier runs on a single model.

## [0.1.0] — 2026-06-20

Initial release. The cheap, installs-anywhere core of the mango ticket-lifecycle harness.

### Added
- **Marketplace** `mango-plugins` with the `mango` plugin (`source: ./plugins/mango`).
- **Six gated lifecycle skills:** `analysis`, `design`, `execute`, `review`, `finalise`, and the
  `solve` orchestrator — each grounded at runtime in `.harness.json` and `PRINCIPLES.md`.
- **Three read-only agents:** `reviewer` (rule-book verdict), `challenger` (ticket-blind), and
  `onboarder` (wayfinding).
- **Templates:** the per-ticket working doc and the PR body.
- **`PRINCIPLES.md`** — the binding contract: think before coding, simplicity first, surgical
  changes, goal-driven execution.
- **`config/harness.example.json`** — the per-project contract users copy to `.harness.json`.
- **Production hygiene:** stdlib-only `scripts/validate.py`, a GitHub Actions `validate` workflow,
  `.gitignore`, MIT `LICENSE`, and two READMEs.

### Out of scope (planned for v2)
- Stack-specific building-block skills (trace / new-module / db-patch / modernize).
- The enforcement layer (write-time hooks, a CI static-check mirror, a worktree fleet).
