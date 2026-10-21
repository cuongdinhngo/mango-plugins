# CLAUDE.md — standing context for working in mango-plugins

<!-- mango:standing-context (the same hoist `/mango:init` writes into a consuming project — kept by hand here, because this repo IS the plugin) -->

Read this before editing anything under `plugins/mango/`. It carries the constraints that hold across
every session, and **pointers** to the sources of truth — never a copy of them (a copy goes stale and
competes with the source).

## What this repo is

A Claude Code **marketplace** whose root *is* the marketplace; the `mango` plugin lives in
`plugins/mango/`. mango ships machinery only: every project-specific rule is read at runtime from that
project's `.harness.json`, so nothing here may assume a stack, a tracker, or a language.

## The gates, and when each applies

| | command | when |
|---|---|---|
| Cheap, always-on contract guard | `python3 scripts/validate.py` | after **every** edit; must print `OK` and be green before any push (CI runs it on push/PR) |
| Harness script suite | `python3 tests/envelope/test_envelope.py` | after touching `plugins/mango/scripts/`; deterministic, free, no dispatch (CI runs it on push/PR on Linux **and** on Windows at the default console code page; the smoke guard runs it too) |
| Per-skill smoke guard (costs tokens) | `bash tests/eval/run.sh --only '^(<fixture>\|…)$'` | on an edit under `skills/`, `agents/`, `principles/` or `templates/`: the fixtures mapped to the edited skill in `FIXTURE_SKILLS`, before merge. Anchor the selector |
| Whole guard (optional) | `bash tests/eval/run.sh` | all seven fixtures, ~7 dispatches, ~$3.50 — at a milestone |

**mango has no behavioural regression suite.** The 126-job suite was retired in 1.16.0; what remains is
the seven-fixture smoke guard. A green guard means *the selected fixtures passed just now* — it detects
no cross-skill regression and does not cover `RETIRE:`. Never call it "the eval is green".

The guard dispatches concurrently, each worker in its own throwaway clone; the live checkout is never
touched and a post-run guard asserts it. `--workers 1` is the sequential mode for debugging one
transcript.

**Commit a skill edit before running the guard.** Each clone is of HEAD, so an uncommitted change is
invisible to every fixture and its fixture fails against the old shipped text. Commit locally, run,
amend if red — pushing is always a separate, approved step.

**Run the guard CACHE-FIRST during a build.** Use `--no-cache` only to prove a **new** assertion 3×
fresh (`--no-cache --only '^(<new-fixture>)$'`, run sequentially — parallel runs share `.transcripts/`)
or for a milestone run of the whole guard. Editing `run.sh` or any `agents/*.md`, `PRINCIPLES.md` or
template invalidates every fixture's cache by design.

**`main` is the release channel.** The community-marketplace pin advances on every push to `main`, so a
merge ships. Merge only with the deterministic gates green on the merged commit and the smoke guard run
for every skill the change edited (`CONTRIBUTING.md` → *`main` is the release channel*).

**On Windows**, `python3` may be the Microsoft Store stub rather than an interpreter; run the gates with
`py -3` (or `python`) instead.

## Standing constraints (they hold in every session)

- **The human holds every gate.** Silence is never approval; never self-approve; no outward action
  without a separate explicit approval per action.
- **false-green is the #1 risk.** The whole design exists to prevent "looks done but isn't." An
  over-claimed CHANGELOG, or a validator green on a false claim, is the worst class of defect — worse
  than a visible red.
- **Counted artifacts bind.** A decision counts only when emitted as a falsifiable, gate-blocking
  artifact — never as prose.
- **Prose IS behaviour.** A `SKILL.md` is runtime-loaded: editing its words changes what mango does.
  Treat a skill edit as a behaviour change and verify it behaviourally, through the smoke guard's
  fixtures for that skill (and a new fixture when the change adds a behaviour none covers) — never a
  live patch.
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
- `CONTRIBUTING.md` — how to validate, the smoke-guard discipline, `main` as the release channel, and
  the **release checklist** (version bump → CHANGELOG entry → root README badge → the Maturity claims).
- `tests/eval/README.md` — the seven fixtures and the skill each is mapped to, the assertion convention
  (match the decision, be emphasis-agnostic, 3× fresh, widen over wording never over outcome), the last
  full run, and how the cache and dispatch-free self-tests work.
- `plugins/mango/principles/maturity.md` — which behaviours are **Experimental** (the single source; a
  README never restates the labels).
- `plugins/mango/CHANGELOG.md` — what changed per version; the neutral source for a retro.

<!-- /mango:standing-context -->
