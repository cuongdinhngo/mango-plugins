# CLAUDE.md — standing context for working in mango-plugins

<!-- mango:standing-context (the same hoist `/mango:init` writes into a consuming project — kept by hand here, because this repo IS the plugin) -->

Read this before editing anything under `plugins/mango/`. It carries the constraints that hold across
every session, and **pointers** to the sources of truth — never a copy of them (a copy goes stale and
competes with the source).

## What this repo is

A Claude Code **marketplace** whose root *is* the marketplace; the `mango` plugin lives in
`plugins/mango/`. mango ships machinery only: every project-specific rule is read at runtime from that
project's `.harness.json`, so nothing here may assume a stack, a tracker, or a language.

## The two gates, and when each applies

| | command | when |
|---|---|---|
| Cheap, always-on contract guard | `python3 scripts/validate.py` | after **every** edit; must print `OK` and be green before any push (CI runs it on push/PR) |
| Behavioural eval (costs tokens) | `bash tests/eval/run.sh --workers 8` | **once** at the end of a change, before push |
| Dev loop during a build | `bash tests/eval/run.sh --only <regex>` | affected fixtures only — a **PARTIAL** run that never substitutes for the full suite |

The eval dispatches concurrently, each worker in its own throwaway clone; the live checkout is never
touched and a post-run guard asserts it. `--workers 1` is the sequential mode for debugging one
transcript. Editing `run.sh` invalidates the whole transcript cache by design, so the next run is fresh.

**Each clone is of HEAD, so commit a skill edit before running the eval.** An uncommitted change is
invisible to every fixture, and the fixture for it fails against the old shipped text. Commit locally,
run, amend if red — pushing is always a separate, approved step.

## Standing constraints (they hold in every session)

- **Prose IS behaviour.** A `SKILL.md` is runtime-loaded: editing its words changes what mango does.
  Treat a skill edit as a behaviour change and verify it behaviourally.
- **Skills are directive-only** — the rule goes in the skill, the reason in
  `plugins/mango/CHANGELOG.md`, the incident in `plugins/mango/RATIONALE.md` (loaded by no skill).
  Enforced by `validate_no_rationale_in_skills`.
- **Never remove a CHECK.** Every change adds or strengthens; no gate is loosened, no assertion
  narrowed. Widen an eval assertion over *wording or emphasis* only — never over outcome.
- **The human holds every gate.** Silence is never approval, and no outward action happens without a
  separate explicit approval per action.
- **Project-agnostic, English-only, public repo.** Fixtures use `PROJ-*` keys and no real project,
  ticket, library, framework, or brand. No secrets anywhere — not in config, docs, or fixtures.
- **Verify before push**, and show the verification output rather than asserting it passed.

## Pointers (the sources of truth)

- `plugins/mango/PRINCIPLES.md` — the binding contract: the four principles, the descriptive/normative
  boundary, git isolation, maturity vocabulary, model delegation, the token-cost axis.
- `CONTRIBUTING.md` — how to validate, the eval discipline, and the **release checklist** (version bump
  → CHANGELOG entry → root README badge → the Maturity claims).
- `tests/eval/README.md` — the assertion convention (match the decision, be emphasis-agnostic, 3×
  fresh, widen over wording never over outcome) and how the cache and the dispatch-free self-tests work.
- `plugins/mango/CHANGELOG.md` — what changed per version; the neutral source for a retro.

<!-- /mango:standing-context -->
