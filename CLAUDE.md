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
| Behavioural eval (costs tokens) | `bash tests/eval/run.sh --workers 8` | **once** at a milestone, before push |
| Dev loop during a build | `bash tests/eval/run.sh --only <regex>` | affected fixtures only — a **PARTIAL** run that never substitutes for the full suite |

The eval dispatches concurrently, each worker in its own throwaway clone; the live checkout is never
touched and a post-run guard asserts it. `--workers 1` is the sequential mode for debugging one
transcript.

**Commit a skill edit before running the eval.** Each clone is of HEAD, so an uncommitted change is
invisible to every fixture and its fixture fails against the old shipped text. Commit locally, run,
amend if red — pushing is always a separate, approved step.

**Run eval CACHE-FIRST during a build** — only fixtures whose changed skills are touched run fresh; let
the cache skip the rest. Use `--no-cache` ONLY for the final milestone verification, never on every
iteration (a full-fresh build once cost ~72M tokens / $70). Editing `run.sh` invalidates the whole
cache by design, so avoid touching it unless necessary.

## Standing constraints (they hold in every session)

- **The human holds every gate.** Silence is never approval; never self-approve; no outward action
  without a separate explicit approval per action.
- **false-green is the #1 risk.** The whole design exists to prevent "looks done but isn't." An
  over-claimed CHANGELOG, or a validator green on a false claim, is the worst class of defect — worse
  than a visible red.
- **Counted artifacts bind.** A decision counts only when emitted as a falsifiable, gate-blocking
  artifact — never as prose.
- **Prose IS behaviour.** A `SKILL.md` is runtime-loaded: editing its words changes what mango does.
  Treat a skill edit as a behaviour change and verify it behaviourally, through the normal build+eval
  path — never a live patch.
- **Skills are directive-only** — the rule goes in the skill, the reason in
  `plugins/mango/CHANGELOG.md`, the incident in `plugins/mango/RATIONALE.md` (loaded by no skill).
  Enforced by `validate_no_rationale_in_skills`.
- **Never remove a CHECK.** Every change adds or strengthens; no gate loosened, no assertion narrowed.
  Widen an eval assertion over *wording or emphasis* only — never over outcome.
- **Harness, not rules.** mango is an empty machine; the PROJECT supplies every rule via its
  `.harness.json`/rulebook. mango assumes no stack/tracker/language and carries no project's context home.
- **descriptive-generate / normative-facilitate / never-author-normative.** mango describes what exists
  and facilitates the human choosing rules; it never writes the rules itself.
- **Lessons never modify mango.** No lesson — however ratified — edits a mango skill. A skill-gap is a
  signal for the maintainer; mango changes only through a normal version. (A lesson flowing into a skill
  would break harness-not-rules and destroy provenance — you couldn't tell mango's own design from an
  injected check.)
- **layer-match.** Sensitive layers (auth, DB, deletion, anything irreversible) demand heavier proof
  than a unit-mock.
- **Project-agnostic, English-only, public repo.** Fixtures use `PROJ-*` keys and no real project,
  ticket, library, framework, or brand. No secrets anywhere — not in config, docs, or fixtures.
- **Verify before push**, and show the verification output rather than asserting it passed.

## Pointers (the sources of truth — never copied here)

- `plugins/mango/PRINCIPLES.md` — the binding contract: the four principles, the descriptive/normative
  boundary, git isolation, maturity vocabulary, model delegation, the token-cost axis.
- `CONTRIBUTING.md` — how to validate, the eval discipline, and the **release checklist** (version bump
  → CHANGELOG entry → root README badge → the Maturity claims).
- `tests/eval/README.md` — the assertion convention (match the decision, be emphasis-agnostic, 3× fresh,
  widen over wording never over outcome), and how the cache and dispatch-free self-tests work.
- `plugins/mango/CHANGELOG.md` — what changed per version; the neutral source for a retro.

<!-- /mango:standing-context -->
