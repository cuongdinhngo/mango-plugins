# Changelog

All notable changes to the mango plugin are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

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
