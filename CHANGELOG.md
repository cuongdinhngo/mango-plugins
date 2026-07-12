# Changelog

All notable changes to the mango plugin are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

## [1.3.1] — 2026-07-12

Eval-truth patch — no skill behaviour changes. The `red-baseline` fixture previously narrated a red
baseline in prose while the sandbox's `config.test_command` was `true` (always green), so a correct
detect-not-assume run *measured* green and the assertion missed, while any pass came from the model
**narrating** "red" off the ticket rather than measuring it — green for the wrong reason. This release
makes the baseline **genuinely** red so Fix #3 is actually exercised.

### Changed
- **`red-baseline` fixture now measures a genuinely red baseline.** `tests/eval/run.sh` parameterizes
  the sandbox harness on `test_command` (`write_harness`) and, for the `red-baseline` fixture only,
  points it at a **committed pre-existing failing check** (`tests/baseline/verify.sh`, exits non-zero
  on a clean checkout on an item outside the ticket's area), then restores the green default. The
  fixture ticket no longer carries any fabricated command output, and the failing-item detail
  (`pdf_snapshot_spec` / snapshot drift / sub-pixel / "1 failed") lives **only** in the command output
  — so its presence in a transcript proves the baseline was **measured, not narrated**.
- **Decision-level assertions for `red-baseline`:** detects `baseline: red` **by measuring** (observed
  failing item appears) + DoD is delta-green + the pre-existing failure is a recorded exclusion that
  neither blocks forever nor silently passes. A run that reads "red" off the ticket without running the
  command now fails.

## [1.3.0] — 2026-07-11

Makes mango's token cost **visible and measurable** and adds a human-gated way to adopt an external
token optimizer with its safety trade-offs explicit — without mango ever installing one, depending on
one, or letting one weaken a critic. Cost was always an **estimate**, never measured per-phase; this
release measures first (`context ≠ correctness` applied to optimization: don't optimize what you
haven't measured), then gates adoption behind a human choice exactly as `codify` gates the rule book.
Generic and stack-agnostic throughout — no project, ticket, library, or brand is named; the optimizer
names (RTK / Headroom / Caveman) are the generic classes the safety axis reasons about. Backend
behaviour is otherwise unchanged, and with `token_optimizer` at its defaults a run is identical to
v1.2.

### Added / Changed
- **Cost ledger (descriptive measurement).** The run records token usage **per phase and per subagent
  dispatch** (reviewer, challenger, extractor, Explore fan-out, each review round) into the working
  doc as a **facts-only** counted artifact (new *Cost ledger* block in the working-doc template);
  `solve` records rows as it goes and `finalise` surfaces a one-line summary (total + top cost driver).
  It is **descriptive, never normative** — it makes cost visible so a *human* can decide where to trim;
  it never itself cuts a check, a gate, a critic, or evidence detail. It is also the data a later
  middle-tier sizing decision needs — measure before you size. `PRINCIPLES.md` documents it.
- **`budget` skill (detect + inform + human-gate optimizer adoption).** New `skills/budget/SKILL.md`,
  mirroring `codify`'s descriptive + human-gated shape: it **detects** which optimizers are present
  (installs nothing), **informs** per a fixed **safety axis** (an optimizer is safe only if it removes
  representation redundancy — how output is phrased — never a check, gate, critic, or the evidence a
  critic relies on), **human-gates adoption** into a `token_optimizer` block in `.harness.json` as a
  **recorded provisional decision** (ratified like `codify`), and **reports** each enabled optimizer's
  estimated/measured saving in the ledger (measure the optimizer, don't trust its claim). It never
  installs, never makes mango depend on an optimizer, and never silently changes what a critic emits.
- **RTK default-expect (below mango; degrade cleanly).** The default `token_optimizer.rtk: "expect"`
  means mango **tolerates** RTK rewriting Bash-command output (git/test/lint/ls) into a compact form —
  it does **not** install RTK and does **not** require it. RTK absent → everything runs **identically**
  (only the saving is lost); mango never fails, blocks, or changes a decision on RTK presence/absence,
  and no mango logic parses an RTK-specific format in a way that breaks without it. `doctor` may note
  RTK presence as one **informational** line (never a gating ✅/⚠/❌).
- **Caveman critic guardrail (HARD — invariant).** Caveman-style output compression **must never** be
  applied to critic output — the `reviewer`, `reviewer-max`, `challenger`, and any gate-blocking
  artifact — which **must retain full evidence detail** (`path:line`, measured values, per-clause
  verdicts). The three critic agent briefs carry the guardrail; Caveman, if enabled, is **scoped to
  non-critic output only** (`caveman.scope: "non-critic-only"`, enforced). `PRINCIPLES.md` states the
  rationale: terse critic output loses the evidence that *is* the review's value; brevity is never
  applied where a false-green could hide (the retro-#5 class).
- **Config, validator & docs.** New `token_optimizer` block in `config/harness.example.json` (with the
  two hard-pinned invariants). `scripts/validate.py` adds the `budget` skill contract (detect / inform
  / recorded / never-install / degrade-clean / non-critic-only tokens), a `token_optimizer` schema
  check (rtk expect, `output_shaper` false, caveman non-critic-only), and a critic-guardrail token
  check across the three critic agents (build fails if the Caveman-critic prohibition is dropped). Both
  READMEs and `PRINCIPLES.md` document `budget`, the safety axis, the RTK expectation, and the ledger;
  the v0.5 doc-consistency check stays green.
- **Eval coverage (one fixture per guarantee).** Four generic fixtures (`ledger-descriptive`,
  `rtk-degrade`, `caveman-critic-guard`, `optimizer-adoption-gated`) assert: a run records a
  facts-only per-phase/subagent ledger and surfaces a finalise summary without auto-cutting; an
  RTK-absent run completes identically with no changed decision; critic output keeps `path:line`
  evidence and the guardrail forbids terse critic output; enabling an optimizer lands in `.harness.json`
  as a recorded provisional choice. Fixtures are generic (`PROJ-*`); the eval coverage header is updated.

## [1.2.0] — 2026-07-11

Four evidence-backed fixes from field retros #4 and #5, gathered into one minor. No new architecture
— all four refine existing mechanisms. Each ships with its **own** generic eval fixture so a red run
pinpoints which fix regressed. Generic and stack-agnostic throughout — no project, library,
framework, formatter, or device is named. Backend behaviour is otherwise unchanged.

### Added / Changed
- **`execute` — design-conformance self-check (scope discipline on BOTH axes).** The verification
  sweep now measures scope on **two axes**: the **file set** (the existing `diff ⊆ approved list`
  sweep) **and** conformance to the **approved design behaviour**. `execute` walks **each Gate-2
  Approach bullet**, classifies it `implemented-as-approved | deviated`, and any `deviated` bullet is
  **recorded as a deviation** (reusing the Phase-3 deviation record) traced to its approved bullet and
  surfaced to `review` — **even when every touched file is inside the change-list**, so the file-set
  sweep passes clean. `review`'s scope reconciliation re-confirms the behaviour axis and treats a
  missed behavioural deviation (or a feature self-marked `✅` that was not implemented) as **not
  clean**. `PRINCIPLES.md` §3 states the two axes. *(Observed, retro #5: Gate 2 approved a behaviour
  in writing, execute implemented something different and recorded no deviation because no file left
  the change-list — a green counted artifact sitting over a wrong behaviour; only the reviewer,
  re-reading the design, caught it.)*
- **`analysis` — vague acceptance value → falsifiable at Gate 1.** Each acceptance value must be
  either **falsifiable** (a measurable/greppable definition, not a vague adjective) **or** recorded as
  an explicit **manual-check exclusion** (unmeasurable → human-verified, logged up front as a
  coverage-gap exclusion). One that is **neither** is flagged by the AC-validation step and **may not
  carry a matrix `✅`** — a bare self-reported `✅` can no longer stand in for an unmeasurable or
  unbuilt thing. Ties into the existing AC-validation + coverage-gap-exclusion machinery; no parallel
  mechanism. `PRINCIPLES.md` §1 documents it. *(Observed, retro #5: a vaguely-worded requirement was
  self-marked `✅` without being implemented, because nothing forced the vague word to a testable
  form.)*
- **Red/flaky baseline vocabulary (`analysis` + `execute` + `review`).** A first-class,
  **project-supplied** baseline: `analysis` runs the verification command once on the untouched
  checkout and records `BASELINE: green | red | flaky` (with the specific failing items). A clean
  checkout is **not** assumed green. When `baseline ≠ green`, the Definition of Done becomes **prove
  the delta is green** — the change introduces no new failure and fixes any it claims to; a
  pre-existing failure outside the change is a **recorded baseline exclusion**, neither a blocker nor
  a silent pass. `execute` proves against the baseline; `review`/`finalise` compare against it, never
  against a blanket "all green". mango **detects and records** the baseline; it never decides which
  pre-existing failures are acceptable (a human/rulebook call, logged). New `BASELINE` field in the
  working-doc template; `PRINCIPLES.md` §4 documents it. *(Observed, n=2: the verification command was
  unsatisfiable on a clean checkout — a pre-existing/flaky failure — and mango had no vocabulary for a
  red/flaky baseline, so the operator improvised "baseline red, my delta green" in every phase.)*
- **`review` — conditional LGTM + verify-only re-review.** Round 1 may return a **conditional LGTM**
  ("LGTM once findings 1–N land as described"); the re-review is then a **verify-only pass** — confirm
  the N named fixes are present + a regression scan — **without** a full requirement re-derivation. The
  ticket-blind `challenger`'s full re-derivation runs **once** and is **not repeated** on a verify-only
  round unless a fix changed scope (its independence is the value; its cost is not paid twice for pure
  re-confirmation). A reviewer may still demand a full re-review if a fix touched something material.
  The `reviewer`/`reviewer-max` briefs describe the conditional-LGTM option. *(Observed, n=2: a round-2
  review after CHANGES REQUESTED was ~100% re-confirmation yet cost a full reviewer+challenger
  re-derivation.)*
- **Eval coverage + validator lock.** Four generic fixtures (`behavioural-drift`, `vague-requirement`,
  `red-baseline`, `conditional-LGTM`) — one per fix, so a red run is diagnosable — assert: a
  behavioural deviation is recorded despite a clean file diff; a vague AC is pinned to a measurable or
  logged as a manual-check exclusion and cannot carry a bare `✅`; a pre-existing failure yields
  `baseline: red` with a delta-green DoD; a conditional LGTM leads to a verify-only re-review.
  `scripts/validate.py` now requires the `analysis` `falsifiable`/`manual-check`/`baseline`, `execute`
  `approved design`/`both axes`/`baseline`, and `review` `conditional`/`verify-only`/`baseline`
  tokens, so none can silently regress. Both READMEs and `PRINCIPLES.md` document all four; the v0.5
  doc-consistency check stays green.

## [1.1.0] — 2026-07-10

One evidence-backed refinement from field retro #4 — the **format-scope rule** — plus the
previously-unreleased eval assertion-robustness work, shipped together. No new architecture; the fix
is one proven refinement to the existing surgical discipline. Generic and stack-agnostic — **no
formatter is named**. Backend and non-frontend behaviour is otherwise unchanged.

### Added
- **`execute` — the format-scope rule, stated explicitly.** `execute` now states it: run the
  project's formatter **only on the files this change authored or edited**; **never** reformat a
  shared or pre-existing file wholesale. A whole-file format pass rewrites lines outside the change
  and reads as scope creep at review; whole-file conformance is a **separate concern** — CI, or a
  dedicated chore ticket — never folded into this ticket's diff. It is the existing untouched-lines /
  surgical discipline (Principle 3) applied to the formatter, not a parallel rule. `review`'s scope
  reconciliation now names a wholesale reformat of a shared file as **not clean**; `PRINCIPLES.md`
  (Principle 3) and both READMEs document it. *(Observed, retro #4: a whole-file format pass over a
  shared file reformatted untouched lines → review flagged scope creep → the reformat was reverted →
  the next whole-file pass re-collapsed it — a real, recurring loop. The by-hand resolution — format
  only the authored/edited files — was not stated as a rule, so it recurred.)*
- **Eval coverage + validator lock.** A generic `format-scope` fixture asserts `execute` scopes the
  formatter to the authored/edited file and does **not** wholesale-reformat the shared file present
  beside it. `scripts/validate.py` requires the `execute` `format[ -]scope` token so the rule cannot
  silently regress.

### Changed
- **Eval assertions hardened to decision-level + emphasis-agnostic.** Assertions now match the
  *decision* (outcome token + reasoning token both required) and tolerate markdown emphasis (`**`/`_`)
  and phrasing variants around the load-bearing token, so a correct behaviour passes under any wording
  while a wrong *outcome* still fails. The `lite: TIER lite` regex was the last brittle instance
  (`TIER:[[:space:]]*lite` → `TIER:[[:space:]*_]*lite`); the stale-review assertions were widened the
  same way earlier. Widening is over *wording/emphasis only*, never over outcome — every assertion
  still fails on a wrong tier / a missed exemption / an honoured bare "go".
- **Certified stable across independent fresh runs.** `tests/eval/run.sh` was run **6 consecutive
  times end-to-end**, each regenerating transcripts — all **33/33**, no assertion failing on any run.
  Green now reflects run-to-run stability, not a regex tuned to a single already-produced transcript.
- **READMEs document the assertion-robustness property** in their eval sections (both the root and
  plugin READMEs).

## [1.0.0] — 2026-07-08

The **official 1.0 release**. Three evidence-backed sharpening fixes from the latest field retro —
all refinements to existing mechanisms, no new architecture — plus the stable-API milestone. Generic
and stack-agnostic throughout; backend and non-frontend behaviour is unchanged.

**Release status (honest).** The public skill/config API is **stable**. mango has been proven
end-to-end across multiple real projects and two stacks **by its author**, with a green behavioural
eval suite and fault-injected escalation paths. **Independent-operator validation is ongoing** and
its results will be folded into later releases.

### Fixed
- **`execute` frontend track — one assertion PER CLAUSE of a multi-clause M-gate.** A multi-clause
  rubric gate (M4 = touch-target `size ≥ 44×44 px` **and** `spacing ≥ 8 px`; M7 = focus indicator
  `visible` **and** `contrast ≥ 3:1`) is only proven when **every clause** carries its own assertion.
  `execute` now enumerates **one assertion per clause** and the proof manifest carries **one row per
  clause**; a clause with no assertion makes the gate **incomplete → it blocks, exactly as a missing
  surface does**. This generalizes the per-item-inventory rule (which prevents aggregate-count hiding)
  from surfaces to the clauses of a gate. `templates/frontend-rubric.md` names the clauses of each
  multi-clause gate; `execute` enumerates them and invents none. *(Observed: an M4 proof asserting
  only the size clause shipped green while a real 0 px-gap spacing failure went unproven.)*
- **`design` — mechanical test blast-radius sub-step in the Gate-2 plan.** Before closing the change
  list, `design` now **mechanically enumerates the existing assertions the change will invalidate** —
  grepping for the copy keys, headings, route shapes, or exports being changed — and **folds each hit
  into the approved change list as up-front proof collateral**. This converts a predictable execute
  deviation (an existing test asserting an old string) into a planned Gate-2 item. *(Observed: a
  change reworded a heading an existing shell test asserted; the change list never mentioned that
  test, so it surfaced only as an execute deviation.)*
- **`version-check` — follow `source` to the plugin's own `plugin.json` when the manifest has no
  `version`.** A marketplace manifest often carries no `version` field — the version lives in the
  plugin's `plugin.json`. Step 2 now follows the plugin's `source` path to its `plugin.json` and reads
  the version there instead of dead-ending at "not specified". Still **detect-and-inform only** — a
  read, never a self-update. *(Observed: the skill dead-ended on a version-less manifest and the
  operator had to fetch the published `plugin.json` by hand.)*
- **Validator + eval locked to the new semantics.** `scripts/validate.py` now requires the `execute`
  per-clause token (`(per|each) clause`), the `design` `blast[ -]radius` token, and the `version-check`
  `plugin.json` fallback token, so none can silently regress. Two generic fixtures added
  (`per-clause`, `blast-radius`): an M4 proof asserting only size marks the spacing clause unproven and
  **blocks Gate 2** while a both-clause proof passes; a string-altering change lists the affected
  existing test in the Gate-2 change list as collateral.

## [0.9.1] — 2026-07-07

Test-infra / docs only — **no skill behaviour changes**; the 27 behavioural assertions stay green,
now runnable by anyone in one command. Closes the "eval repeatable-by-others" gate.

### Added / Changed
- **"Running the eval" note in the README.** Documents the local one-command run
  (`bash tests/eval/run.sh`) for a second person cloning the repo: it works with **either** an
  exported `ANTHROPIC_API_KEY` **or** an OAuth/subscription login, sets up and tears down its own
  throwaway environment, runs against the shipped skills via `--plugin-dir`, and prints
  `N/N assertions pass`. The auth-agnostic guard and self-scaffolding runner themselves shipped in
  0.8.1; this makes the hands-free, any-auth path explicit for local operators, not just CI.

## [0.9.0] — 2026-07-07

Makes the finalise **stale-review guard** mechanical. The guard already *behaved* correctly — it lets
a working-doc bump through, refuses on a source change, and resists a bare "go" — but only because the
model **reinterpreted** the step-1 prose. Read literally, that prose dead-locked every full-tier run:
its "if commits landed after the reviewed SHA" clause always matches, because the commit that records
`Reviewed at <sha>` necessarily lands *after* the SHA it names. This replaces judgment-dependent prose
with a deterministic rule. No change to what fires — only to how the rule is stated.

### Fixed
- **Stale-review guard is now a file-set test, never a commit-count test.** `finalise` step 1 computes
  the changed set (`git diff --name-only <Reviewed-at-sha>..HEAD` ∪ working-tree diff), **exempts** the
  working-doc / bookkeeping path(s) — derived deterministically from `work_doc_mode`/`work_dir` and the
  path now recorded with the marker — and is **stale iff any remaining source file is beyond the
  reviewed set**. The "any commit after the SHA" criterion is deleted, so the marker/bookkeeping bump
  can no longer dead-lock the guard. A bare "go" still never clears it; only a fresh `Reviewed at`
  marker covering the current tree does.
- **Marker now records the working-doc path.** `review` writes the working-doc path alongside the
  `Reviewed at <sha>` marker + reviewed-file set, making finalise's exemption unambiguous.
- **Docs + validator synced.** `solve` and `PRINCIPLES.md` describe the guard mechanically (source
  beyond the reviewed set = stale; working doc exempt). `scripts/validate.py`'s `finalise` contract now
  also requires the `beyond the reviewed set` and `exempt` tokens, so the rule cannot regress to a
  commit-count phrasing.
- **Eval coverage (both directions).** Two generic fixtures added: a working-doc/marker-only bump must
  **proceed** (the regression test for the literal dead-lock, which occurred on every full-tier run),
  and a source file changed beyond the reviewed set must **refuse**, route back to `review`, and resist
  a bare "go".

## [0.8.1] — 2026-06-28

Test-infra only — **no skill behaviour changes**. Makes the behavioural eval
(`tests/eval/run.sh`) runnable by anyone with one command, regardless of how they authenticate.

### Fixed
- **Eval runnable via OAuth or API key.** The runner required `ANTHROPIC_API_KEY` and rejected a
  perfectly capable OAuth/subscription session. The guard now verifies the *capability* to run
  `claude -p` — API key, else a non-interactive `claude auth status` check, else a minimal capability
  probe — and only fails (naming **both** options) when none works. Never rejects an OAuth session.
- **Hands-free self-scaffolding.** `run.sh` now sets up its own throwaway environment (an isolated
  local clone + a temp gitignored `.harness.json` + a minimal rule book) and runs the fixtures against
  the **shipped** skills via `--plugin-dir`, so a fresh clone exercises what the repo ships rather than
  whatever the operator has installed. Everything is removed on exit (`trap`), and fixtures that
  `execute` can only mutate the throwaway clone — the live checkout is never touched.
- **CI uses the same single code path.** `eval.yml` still just runs `bash tests/eval/run.sh` (API key
  from the secret in CI, OAuth locally) — no CI-only branch.

All fixtures and assertions are unchanged.

## [0.8.0] — 2026-06-27

Surface-coverage + tiered UI proof, built **on top of** the v0.7 frontend gates (reusing `track`,
`TIER`, the layer-match hard gate, the per-AC verification plan, the counted-artifact pattern, the
opt-in `sitemap`, and the existing exclusion record — no parallel mechanism). On two real frontend
field tests the full pipeline went **green and still shipped broken UI** — under *opposite* harness
conditions (one with full e2e, one with none). The shared root cause was **not** weak proofs: it was a
**wrong denominator on the surface axis** — the verification counted the surfaces the *ticket* named,
while the failures lived on reachable surfaces the ticket never mentioned. A green gate proved the
wrong N. Generic and stack-agnostic throughout — no framework, library, test-runner, product, or
device specifics ship. Backend is untouched, and a frontend ticket with no integration/runtime AC runs
exactly as in v0.7.

### Added / Changed
- **S1 — Surface coverage: N comes from the CODE, not the ticket (the fix).** For a universal /
  app-wide frontend requirement (no horizontal scroll, reflow, focus-visible, contrast — anything
  phrased all/every/no or inherently page-wide), `analysis` enumerates **every reachable surface**
  (route / full-window overlay / modal / major mounted state) from the code surface — the opt-in
  `sitemap` (`config.docs_dir/sitemap.md`) if present, else a read-only "enumerate reachable views"
  sub-step — and emits a counted, challenger-checkable `SURFACES: N`. The ticket's examples are a
  **hint, never the denominator**. New surface-inventory slot in the working-doc template; validator
  requires the `analysis` `SURFACES` token. *(Observed: "I tested the surfaces the ticket named" passed
  the gate while reachable surfaces the ticket never mentioned shipped broken.)*
- **S2 — Elastic proof tier: e2e optional, a proof not.** A frontend AC's risk-layer proof is
  satisfied by the **highest available tier**, recorded per surface in a **proof manifest** beside the
  verification plan: `PASS(automated)` (tier-1, satisfying the **C1–C8** automated-proof contract by
  composing the *project's* declared runner — detected from declared test scripts / `config.test_command`,
  **mango bundles none**) → `PASS(render@<bp>)` (tier-2, a recorded render of the real surface at the
  breakpoint asserting the visible measurable — a **first-class proof, NOT an exclusion**, the cheap
  reality-facing check both field tests were missing) → `EXCLUDED(approver, reason)` (only when neither
  tier is reachable; reuses the v0.6/T2 exclusion record). `execute` **never stops for a missing
  runner** — it scaffolds tier-1 per the new runner-agnostic `templates/ui-proof-scaffold.md`, else
  records a tier-2 render proof, else an exclusion. Dropping a tier because there is no runner is fine;
  dropping to *nothing* blocks the gate. Validator requires the `execute` `render` / `proof-manifest` /
  `ui-proof-scaffold` tokens. *(Observed: with no test runner, the proving-test gate degraded to a
  silent exclusion instead of demanding the one cheap proof that exists — render the surface and look.)*
- **S3 — Counted `N == M + X` gate + loud banner.** `design` lays out the verification plan / manifest
  **one row per (AC × affected surface)**; `review`'s challenger scores each entry (tier-1 vs C1–C8,
  tier-2 vs the render-proof contract) and **re-runs ≥1** tier-1 `proof-cmd` (or confirms a tier-2
  render artifact) to defeat fabricated entries. With `N` = |surfaces|, `M` = surfaces with a valid
  PASS (any tier), `X` = recorded EXCLUDED, **the gate passes iff `N == M + X`** — otherwise
  `design`/`review` emit `⚠ surfaces proven: k/N — <uncovered> have no proof; cover or record an
  exclusion` and block, as unmissable as an unfilled matrix column. The challenger keeps its
  ticket-blindness: it re-enumerates surfaces from the branch code rather than reading the working-doc
  manifest. Under `TIER=lite` the re-run lightens to confirming command/artifact presence — coverage,
  the manifest, and a proof per surface stay mandatory. New generic eval fixtures assert the `k<N`
  block and the no-runner `PASS(render@<bp>)`. Validator requires the `review` `proof-manifest` /
  `surfaces proven` tokens. mango **owns** the coverage rule, tier ladder, manifest schema, and
  scaffold spec; it **composes** the runner and bundles none.

## [0.7.0] — 2026-06-27

A new **frontend track**: an opt-in gate set for UI work, riding the v0.6 layer-match hard gate
rather than forking it. The design boundary throughout is **own the durable, compose the volatile** —
mango embeds only UI knowledge that is **measurable or greppable** (a11y thresholds, token-first,
conformance to a per-project `DESIGN.md`) and **composes, never owns,** the aesthetic-generation
layer: it calls an external taste skill if one is installed, else follows `DESIGN.md`, and **never
stops because a taste skill is missing.** mango blocks on a missing *number*, never on a missing
aesthetic. The backend path is unchanged: a `track=backend` ticket runs exactly as in v0.6. Generic
and stack-agnostic throughout — no framework, library, product, or device specifics ship.

### Added / Changed
- **F1 — `track` config + TRACK artifact (orthogonal to TIER).** New `track`
  (`backend|frontend|fullstack`, default `backend`) selects which gate set applies; `analysis` emits
  `TRACK: … — k/N touched files under UI paths` as a **counted artifact** the challenger can check,
  using `config.track` or inferring from touched-file paths. `track` is **orthogonal to TIER** (TIER
  = process weight, track = which gates), so a ticket may be `track=frontend` + `TIER=lite`;
  `fullstack` applies both gate sets. When a declared `breakpoints` width is a small viewport, the
  width-parametric gates (M2/M3) are noted in scope. New optional `breakpoints` and `design_doc_path`
  keys. New `TRACK` field in the working-doc template; validator requires the `analysis` `TRACK`
  token.
- **F2 — per-project `DESIGN.md` contract.** On the frontend track, `design` creates/updates a
  `DESIGN.md` (at `config.design_doc_path`) from a new `templates/design-doc.md`: palette derives
  from **domain meaning first, general rules second** (a blanket "ban colour X" yields to a domain
  term that denotes that colour); a **shell** (character-rich) vs **data-core** (tables/grids/charts,
  legibility-first, static) split; and a generic **Responsive & touch** section (declared
  breakpoints, narrow-width navigation pattern, which regions collapse vs reflow vs
  scroll-in-container, thumb-zone, motion). These are project **choices** the gates are scored
  against — they live in `DESIGN.md`, never gated by mango. Validator requires the `design`
  `DESIGN.md` / `data-core` / `responsive` tokens.
- **F3 — falsifiable a11y/token + M1–M10 responsive/touch rubric.** A new
  `templates/frontend-rubric.md` the `review` skill injects into the reviewer/challenger brief when
  track includes frontend (the agents stay generic — no per-track fork). Every item is **falsifiable**
  (measurable or greppable) and scored **against `DESIGN.md`** — "is it tasteful?" is out of the
  rubric. Core items (token-first, no hardcoded hex/px, semantic HTML, state-not-by-colour-alone,
  reduced-motion) plus the **M1–M10** gates (viewport/zoom, no horizontal scroll at each breakpoint +
  the 320 px floor, reflow @320 px, touch-target ≥ 44×44 px, input-zoom ≥ 16 px, tap/hover parity,
  focus-visible, contrast, safe-area, pointer-input parity). Constants (44/24 px, 16 px, 4.5:1,
  320 px) are **standards**, not config.
- **F4 — frontend ACs ride the layer-match hard gate (reused, not forked).** A
  "renders/responsive/contrast/a11y" AC has an integration/runtime (or `document`/`computed-style`)
  risk layer; a unit-only proof against a mocked DOM is a layer-match `❌` and **blocks Gate 2** —
  clearing only with a proof against a **real rendered DOM** (or the served document for the
  viewport-meta gate) or a recorded human-approved coverage-gap exclusion. A **risk-layer floor**
  puts `document`/`computed-style`/`integration-runtime`/`behavioral` all above the logic/unit layer.
  `review` re-confirms no frontend AC closed clean on a layer-mismatched proof. `execute` goes
  **token-first** (all colour/spacing/radius/font through tokens; no scattered hex/px) and
  **input-agnostic** (Pointer Events, no affordance gated solely on `:hover`). **M10 degrades
  gracefully:** an always-on greppable smell (mouse-only / hover-only) can block, while the
  best-effort pointer/touch dispatch-assert runs only when the environment can — else it is recorded
  as a coverage-gap exclusion and never wedges the gate. New generic eval fixtures assert the @320 px
  unit-proof block and the hover-only/mouse-only flag. Validator requires the `execute`
  `token-first`/`pointer` and `review` `a11y`/`DESIGN.md`/`touch-target` tokens.

## [0.6.0] — 2026-06-24

Four fixes from a real run where the gates caught a 4× scope explosion but one of the most
load-bearing checks was **advisory, not binding** — so a worthless proof was allowed to stand. The
theme of this release is mango's own binding contract made literal: prose and self-declared columns
do not bind; only an emitted artifact that **blocks a gate** binds. Every fix is generic and
stack-agnostic; no existing behaviour was removed.

### Added / Changed
- **N1 — Layer-match becomes a hard gate (was advisory).** `design`'s per-AC verification plan now
  requires the **layer-match column to be filled before the proving test is named**, and the rule is
  **binding**: if an AC's **risk layer is integration / runtime / e2e and its proof sits at the
  logic/unit layer**, that row is `❌` and **Gate 2 is blocked** — it passes only when the proof is
  upgraded to the matching layer **or** the row is recorded as a human-approved coverage-gap
  exclusion. The gate keys on the **risk-layer vs proof-layer comparison** (a wording cue —
  "renders / runs / dispatches / persists / sends" — only hints at the risk layer; it is never
  keyword-triage). `review` re-confirms no AC closed clean on a layer-mismatched proof. `PRINCIPLES.md`
  Principle 4 now reads "enforced, not advisory", and `scripts/validate.py` requires the `design`
  binding wording (`layer-match` + a blocking token). *(Observed: a runtime acceptance criterion was
  backed only by a logic-layer unit proof; it passed and proved nothing, because the per-AC
  layer-match check existed but was advisory.)*
- **N2 — Stale-review guard in `finalise`.** A clean review is scoped to the commit it covered.
  `review` now records a **`Reviewed at <sha>` marker** (commit SHA + reviewed files) on a clean
  verdict; `finalise` compares the live `HEAD`/diff against it **before any outward action** and
  **refuses** to open a PR — routing back to `review` for a re-review covering the new diff — if
  commits landed or files changed beyond the reviewed set. A bare "go" does not override a stale
  review. `solve` carries the reviewed SHA across review→finalise and marks the review stale if
  `execute`/`design` re-ran after it. New `Reviewed at` slot in the working-doc template; validator
  requires a `finalise` stale token. *(Observed: a clean review covered a small diff, the diff then
  grew, and finalise opened the PR on the stale review.)*
- **N3 — "Outgrew its ticket" nudge.** `solve` (with light checks in `analysis`/`design`/`execute`)
  tracks the declared `SCOPE`/`TIER`. If at any gate the **realized** scope crosses up a tier
  (especially S/M → L), or the change-list/diff materially exceeds the approved one, mango **stops at
  the next gate** and asks the human to either formally **re-scope** (updating the working-doc scope,
  and the branch/PR type if the change type drifted) or **split** the excess into a follow-up — never
  silently absorbing the expansion. The re-declaration is recorded in the Decision log; validator
  requires a `solve` outgrew/re-scope token. *(Observed: a small card's realized scope grew
  several-fold mid-flow and the working doc absorbed it silently, with the change type drifting from
  the branch type.)*
- **N4 — `init` resolves the config-file commit policy.** After writing `.harness.json`, `init`
  **asks** whether it should be **committed** (shared team config) or **kept local**: on "local" it
  adds `.harness.json` to `.gitignore` (creating it if absent) and tells the user; on "committed" it
  leaves `.gitignore` untouched but warns that secrets never belong in the config (they live in a
  gitignored `.env`). It does not hard-gitignore by default — the config is often shared, so the human
  decides — and never writes secrets into the config file. A note was added to the README Operational
  notes. *(Observed: the per-project config sits at the repo root, so honouring "don't commit it" was
  manual vigilance on every commit.)*

## [0.5.0] — 2026-06-23

The largest feature since v0.1: a facilitated way to **bootstrap a project's rule book** when it is
missing, thin, or inconsistent, plus **opt-in descriptive maps** of the code surface and the database
schema. This closes the single biggest adoption blocker — the rule book the whole plugin grounds in.
Everything here honours one boundary: **mango generates the descriptive and facilitates the normative,
but never authors the normative.** Generic and stack-agnostic throughout; the descriptive maps are
opt-in and never core.

### Added
- **A — `/mango:codify` (facilitated rule/convention definition).** New `skills/codify/SKILL.md`
  observes and **counts** the conventions the code and schema actually use — across generic code
  dimensions (error handling, naming/case, layering, validation, logging, imports) and database
  conventions (table/column naming, timestamps, soft-delete, FK on-delete policy, raw-SQL vs ORM,
  migration style) — flags dimensions with **no dominant pattern** as "no consistent rule found", then
  **asks the human to choose** each going-forward standard. It presents counts as **data** (it may
  state "the majority is X") but **never picks, recommends, or defaults to** any option, and **never
  authors** a rule. Chosen standards are written to `rulebook_path` tagged
  **`PROVISIONAL (awaiting ratification)`** and stay provisional until the human **ratifies** them; an
  optional drift list of diverging files may be emitted as tech-debt. Read-only on code — it changes
  no code. `doctor` now **suggests** `/mango:codify` (suggest only) when the rule book is missing or
  looks thin. `PRINCIPLES.md` states the observe/facilitate/never-author boundary authoritatively.
  *(Observed: with no real rule book, the reviewer/challenger produced generic, low-value output; the
  fix is to help define the standard without mango inventing it.)*
- **B — Opt-in descriptive adapters `/mango:sitemap` and `/mango:db-map`.** Two **descriptive-only**
  skills generate regenerable **facts** (never normative rules), off unless configured and **not** part
  of the lifecycle. `sitemap` maps the code surface (routes/endpoints + modules) via an optional
  `code_map_cmd`; `db-map` maps the schema (tables, columns+types, primary/foreign keys, indexes,
  relationships, views/procedures) via `db_kind` + either `db_introspect_cmd` or `migrations_path`,
  writing to `docs_dir` — read-only, it alters no schema. The *normative* database conventions live in
  the `codify` rule book, not in these maps. Light optional wiring: **if a `db-map` exists**, `analysis`
  may widen the Phase-1 blast radius to schema dependents (columns, FKs, dependent views/procs) — used
  if present, never required; the lifecycle runs fully without either adapter. *(Observed: mango had no
  view of the code surface or the database — where the costliest mistakes live and where the
  reviewer/challenger are blindest — yet schema maps are too stack-specific to be core.)*

### Changed
- **Config.** New optional, generic, commented keys in `config/harness.example.json`: `docs_dir`,
  `code_map_cmd`, `db_kind`, `db_introspect_cmd`, `migrations_path` (all `null`/off by default).
- **Validator.** `scripts/validate.py` skill-contract checks now require the `codify` boundary tokens
  (counting, PROVISIONAL/ratification, does-not-author/recommend). A new **documentation-consistency
  check** asserts that every `skills/*/` directory is named in the plugin README, that the README
  references no `/mango:` skill that does not exist, and that every key in `harness.example.json` is
  documented in the plugin README — failing the build on any doc drift.
- **Docs synced to reality.** The plugin README now carries the full skill inventory (incl. `codify`,
  `sitemap`, `db-map`), an explicit agent inventory, the complete config-key list (incl. the new keys
  and `update_check_url`), and the boundary one-liner; `PRINCIPLES.md`, `plugin.json` `description`, the
  marketplace `README.md`, and the root README were brought into line.

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
