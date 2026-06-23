# Changelog

All notable changes to the mango plugin are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

## [0.4.1] — 2026-06-23

A small, high-value patch from a real run where a preflight reported green while a stale plugin
version was silently loaded, and where a counted "for each of N" requirement shipped with its tail
incomplete. Every fix is generic; mango still **detects and informs, never self-administers** — it
does not install, reinstall, reorder a registry, or run plugin administration on your behalf.

### Added / Changed
- **L — `doctor` surfaces the running version.** `doctor`'s **first output line** is now the
  authoritative running-version signal — `mango <version> @ <base path>`, read from the running
  manifest and base path — with the plain note that a green doctor does **not** prove the intended
  version is loaded, and that a version should be resolved from the host (not by working around the
  loader from a restricted/remote channel). If the base path carries a version segment that differs
  from the manifest, `doctor` emits a mismatch ❌. `doctor` stays **offline**: no network call, no
  reading or editing of any host plugin registry, no install. *(Observed: a preflight passed while a
  stale version ran silently behind it, because the check validated config but never showed which
  version was actually loaded.)*
- **M — Counted "for each of N" requirements become a verified per-item checklist.** `analysis` now
  records a "do X for each of N" requirement as a **per-item checklist** (one row per item) in the
  inventory, not a single aggregate row; `review` verifies it **item-by-item** and is not clean until
  **every** item is confirmed (or each unconfirmed item is a recorded, human-approved coverage-gap
  exclusion) — an aggregate "k/N" alone is insufficient. The working-doc template's inventory gains a
  per-item checklist table. *(Observed: a counted "for each" requirement passed an aggregate check
  with the tail incomplete; only an independent reviewer caught it.)*
- **V — Opt-in `version-check` skill (informs, never updates).** New `/mango:version-check`: reads
  the running version and, **only if** the optional `config.update_check_url` (a raw URL to the
  published marketplace manifest) is set, fetches it to compare against the latest published version.
  When a newer version exists it **prints** the exact host `/plugin` commands to update — it never
  runs them, never installs, and never edits any registry. With `update_check_url` unset it makes no
  network call. New optional `update_check_url` key in `config/harness.example.json`. *(Observed: no
  in-tool way to learn a newer version existed without doing forbidden admin from a restricted
  channel.)*
- **Operational notes (README) + validator.** The plugin README gains an **Operational notes**
  section: plugin administration is the host's job, verify the live version from `doctor`'s first
  line, and use `version-check` to learn of newer versions. `scripts/validate.py` skill-contract
  checks now require the running-version / base-path tokens in `doctor`, item-by-item / per-item
  verification tokens in `review`, a `for each` token in `analysis`, and the `version-check` skill's
  frontmatter, so the new behaviours cannot be silently dropped.

## [0.4.0] — 2026-06-22

Five fixes validated across more than one project and stack. Each describes a generic failure mode
and a universal mechanism — no project, framework, tracker, tool, or filename is baked in. No
existing behaviour was removed; the full tier is unchanged.

### Added / Changed
- **G — Tier triage on the resolved denominator N, not on keywords.** `analysis` now keys the
  lite/full decision on the **resolved inventory denominator N** (from the Phase-1 numbered
  inventory), not on the literal presence of universal wording. A requirement that *sounds* universal
  ("all/every/no") but resolves to **N = 1** is lite-eligible — a single-site change already covers
  "all". `quick`'s hard entry check aligns: it refuses on a universal requirement only when **N > 1**.
  *(Observed: a universal-sounding requirement that resolved to one site forced full tier where lite
  would have sufficed, spending the challenger/reviewer budget on confirmation, not findings.)*
- **H — Project-supplied finalise-checklist hook.** New optional `config.pr_checklist_path` points at
  a project-owned checklist (e.g. a PR-template or definition-of-done file). When set, `finalise`
  reads it before drafting the PR body, walks each item, reports it satisfied / not-satisfied / N-A
  with evidence, and surfaces any unmet item at the final gate. mango supplies the mechanism; the
  project supplies the content. `doctor` warns if the key is set but the file is missing.
  *(Observed: a ship-time requirement mango cannot know was caught only by a project's own checklist,
  not by mango's generic finalise.)*
- **I — Coverage-gap exclusion for proof-tier mismatches.** `design`'s per-AC verification plan now
  requires any row whose proof tier sits below its risk layer to EITHER upgrade the proof OR be
  recorded as a **named, human-approved coverage-gap exclusion** (item · risk tier · why deferred ·
  follow-up). `review` treats a challenger "not met" that corresponds to a recorded exclusion as
  **not a blocker** — an *unrecorded* gap still blocks. New "Coverage-gap exclusions" slot in the
  working-doc template. *(Observed: a requirement whose real risk sat at an integration/behavioural
  tier was only unit-proven, so the challenger's "not met" read as a hard failure when it was a
  proof-tier mismatch.)*
- **J — Conditional working-doc placement (still challenger-blind).** New `config.work_doc_mode`
  (`auto | separate | embed`, default `auto`). A tracker-hosted ticket gets a separate
  `<work_dir>/<KEY>.work.md` (v0.3 behaviour). When the ticket is **itself a local file in the repo**,
  `auto`/`embed` append the working doc to that file **below a clear raw-ticket separator line** — one
  file, no duplicate. `analysis` chooses placement; `review` builds the challenger payload from the
  raw ticket portion only (above the separator) + the diff, never the working-doc portion — the
  challenger-blindness guarantee holds in both modes. *(Observed: a separate working-doc file
  duplicated a ticket that already lived as a repo file.)*
- **K — Full field set on tracker reads.** `analysis` now requests a full field set on a ticket read
  (honouring an optional `config.tracker.fields`, else a sensible default of
  description/body, type, labels, parent, priority) so one read returns the ticket body. *(Observed: a
  tracker read defaulted to a minimal field set and returned an empty description, wasting re-fetches.)*
- **Validator.** `scripts/validate.py` skill-contract checks now require `denominator` in `analysis`,
  `coverage-gap` in `design` and `review`, and `checklist` in `finalise`, so the new behaviours
  cannot be silently dropped.

## [0.3.1] — 2026-06-21

Hardening patch from a review of the built plugin — closing gaps where v0.3 behaviour was asserted
but not *guarded* or *evaluated*. No existing behaviour was removed.

### Added / Changed
- **F1 — Behavioural eval now covers the v0.3 behaviours.** `tests/eval/run.sh` previously exercised
  only `analysis` happy-path artifacts. It now also asserts, via headless `claude -p` (still gated to
  `workflow_dispatch`): proof at the risk layer (`design` marks an integration-layer AC proved only
  by a unit test as a layer-match `❌` and demands an integration/e2e proof), the ticket-blind
  `challenger` catching an unmet AC as "not met" with `path:line`, the design-invalidated escalation
  (STOP + re-open Gate 2), and the stuck-detector (STOP + escalate at the threshold). New generic
  fixtures `design-layer.md` and `challenger-unmet.md`.
- **F2 — `cost_tier: max` has a real Opus-reviewer mechanism.** Because a skill cannot re-pin a
  subagent's model at runtime, the Opus upgrade is now a **choice of agent**: new
  `agents/reviewer-max.md` (identical role/rules/output to `reviewer`, `model: opus`). `review`
  dispatches `reviewer-max` when `cost_tier == "max"` AND the diff is high-stakes (security-tagged,
  or touching auth / data access / schema migration), else `reviewer`; never a Haiku reviewer.
  `PRINCIPLES.md` replaces the vague "upgrade to Opus" wording with this concrete rule.
- **F3 — Right-sizing & escalation are guarded, not advisory.** `quick` gains a **hard entry check
  (step 0)**: it REFUSES and routes to `solve` if the ticket is security-tagged, touches more than
  one file, or has a universal ("all/every/no") requirement. `validate.py` skill-contract checks add
  `TIER` + `design[ -]invalidat` to `solve` and `stuck` to `quick`, so the routing/escalation
  behaviours can't be silently deleted.
- **F4 — Wider reserved-name guard.** `validate.py` `RESERVED_NAMES` now also rejects
  `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, and
  `agent-skills`. `mango-plugins` still passes.

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
