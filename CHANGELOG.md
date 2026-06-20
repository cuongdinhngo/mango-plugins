# Changelog

All notable changes to the mango plugin are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

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
