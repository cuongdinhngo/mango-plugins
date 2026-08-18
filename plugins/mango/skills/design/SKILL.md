---
name: design
description: Phase 2 of the mango ticket lifecycle. Use after analysis clears Gate 1. Produces the approach, rejected alternatives, the smallest change-list traced to matrix rows, rule-compliance check, and the named proving test. Stops at Gate 2.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This phase enforces principle 2 (Simplicity
first) via the smallest change list + `SCOPE`, and principle 4 (Goal-driven) via the named proving
test, the **per-AC verification plan** (proof at the layer where each requirement can fail), and the
**Assumptions** check (no unresolved novel-untested third-party/runtime assumption) — all required
at this gate.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path` and `config.standards_path`. If `.harness.json` is missing, STOP and tell the
user to create one from `<mango>/config/harness.example.json`. No code is written in
this phase.

## Steps

1. **Confirm Gate 1 cleared.** Read the working doc `<config.work_dir>/<KEY>.work.md`. The
   requirements matrix and AC table must be filled and `CLARIFICATION` `j = 0`. If not, return to
   analysis.
2. **Approach + Rejected alternatives.** State the chosen approach in a few lines, then record at
   least one **Rejected alternative** and why (enforces principle 1's record of thought).
3. **Assumptions.** List every assumption the approach leans on, each tagged `verified |
   novel-untested`. For any `novel-untested` assumption about **third-party or runtime behaviour**
   (e.g. "two live editors of library X can coexist", "this API is idempotent under retry"), the
   design must EITHER (a) run a throwaway **spike** now and record the result here, OR (b) shape the
   Gate-2 proving test (step 7) as an integration/e2e proof that would **fail if the assumption is
   false**. **Gate 2 may not pass with an unresolved `novel-untested` assumption.**
4. **Smallest change-list table.** List the minimum set of changes. Columns: change, file/area,
   **blast radius**, `Ph2 covered by` (which matrix row(s)), `k/N`. **Every item must trace to a matrix
   row** — an item with no row behind it fails the gate. Prefer the smallest edit; no speculative
   abstraction, no indirection serving a single call site.

   **The `blast radius` cell — one line per change naming what ELSE it could affect.** For each row,
   name the **side-effect surface**: the callers, shared types, tests/goldens, tool or API descriptions,
   config, migrations, or downstream consumers this change could disturb. Write `none identified` only
   when the mechanical trace below found nothing — never leave the cell blank. It tells the reviewer
   **where to look** beyond the touched file, and a surface named here is exactly what the trace below
   folds into the list as proof collateral.

   **Test blast-radius (mechanical) — trace to REAL producers/consumers, not a shallow name grep.**
   Before closing the change list, **mechanically enumerate the existing assertions and call sites this
   change will invalidate**. A shallow grep of one string in one directory (a table-name in
   `src/**/*.test.*`, or the owning page) **under-scopes** the change and leaves the change-list
   incomplete — so the diff exceeds it at execute. Trace to the **real producers/consumers**:

   - **Change touching a generated/shared TYPE or symbol:** grep by the exported **type/symbol NAME**
     **and its factory/fixture patterns** (test-data builders, mother/factory helpers keyed on that
     type), **enumerate EVERY test root** — not just `src`; include the **e2e / integration test
     roots** and any test dir outside `src` — and run **`typecheck`** (via `config.test_command` or the
     project's typecheck command) as part of the design-time estimate so a type change's real fan-out
     is seen now, not at execute.
   - **VALUE threaded to a downstream consumer** (a value fed into a builder / renderer / prompt-builder):
     enumerate **every builder call site** (every call site of the relevant builder/producer), not just
     the surface/page that owns the feature — the value originates there, so all builder call sites are
     in the blast radius.

   **Fold each hit into the approved change list as an explicit *proof collateral* item** (file/area +
   the matrix row it rides), up front — an existing test whose assertion the change breaks, or a call
   site that produces the threaded value, is a **planned edit**, not an execute surprise. The goal is a
   change-list that is the **smallest COMPLETE set BEFORE execute** — so `diff ⊆ approved change-list`
   holds at execute without deviation-recording having to backfill it. This tightens the **estimate**;
   execute's deviation-recording remains the backstop (it is **not** removed), but it should rarely fire
   for a blast-radius miss once the estimate traces real producers/consumers. A **shallow-grep-only
   estimate that misses a known consumer is a Gate-2 finding.**

   **⭐ Answer every recalled type-2 HANDLE by name (binding — this is the blast-radius step's teeth).**
   `refine`/`analysis` surfaced `<h>` type-2 handles on the `RECALL:` line. Take that list verbatim and
   emit **one row per handle**, naming the handle, and answer each with **exactly one** of:

   - **traced** — paste the **command you ran and its actual output** (trimmed, verbatim, never
     re-typed — the same empirical-output rule `execute` applies) plus what it found: the real
     producers/consumers folded into the change list above, **or** the command's empty result. A row with
     no command and no output is **not** a trace, however confident the prose.
   - **`does not apply because <reason>`** — the literal phrase, where `<reason>` names the property of
     **this** change that puts the handle out of scope (e.g. *"the change adds no shared symbol: the new
     enum is file-local and has no importer"*). This **closes** the handle and is a fully legal answer.

   `HANDLES: <h> recalled | <t> traced (command + result) | <x> does not apply (reason) | <u> unanswered`

   **`u` must be 0 and `h` must equal `t + x`; any `u > 0` BLOCKS Gate 2** — exactly as an unfilled
   matrix column does. Emit the line on **every** run, zeros included: `h = 0` closes it with
   `HANDLES: 0 recalled | 0 traced | 0 does not apply | 0 unanswered` and adds no work whatsoever. A
   recalled handle is **still advisory** — it never becomes a requirement or a matrix row on its own; what
   is binding is that it was **answered**, not what the answer said.
5. **Rule compliance.** Check the proposed change against `config.rulebook_path` and
   `config.standards_path`; note any rule that constrains the design and how you comply.
6. **Verification plan (per-AC, layer-matched) — fill the layer-match column BEFORE naming the
   proving test (step 7).** Emit a table with one row per acceptance criterion / at-risk
   requirement:

   `AC | risk layer (logic | integration | runtime/3p | e2e) | proof artifact (unit | integration | e2e | manual-recorded) | layer-match? ✅/❌`

   Classify each AC's **risk layer** first — the layer where the requirement can *actually fail* —
   then choose its proof artifact to match. A requirement that can only fail at integration/runtime
   (classification cue: worded as "renders / runs / dispatches / persists / sends") cannot be proven
   by a pure-logic test. Do **not** triage on keywords alone — the gate keys on the **risk-layer vs
   proof-layer comparison** the plan records; the wording is only a hint to classify the risk layer.

   **Frontend ACs, surface-aware rows, the under-coverage banner, and the `DESIGN.md` contract
   (frontend track).** When `config.track` includes frontend, **READ
   `<mango>/skills/design/frontend.md` **and** `<mango>/principles/frontend-track.md` NOW** and apply every rule in both: the honest risk-layer
   classification of a frontend AC (a unit-only proof is a layer-match `❌` that blocks Gate 2), **one
   plan row per (AC × surface)** against analysis's `SURFACES: N`, the `⚠ surfaces proven: <M+X>/<N>`
   banner that blocks Gate 2, and creating/updating the project `DESIGN.md` (`config.design_doc_path`,
   covering the palette's domain meaning, the shell vs **data-core** split, and the **responsive** &
   touch choices) **before** this plan is named. This is a **mandatory read**, not a
   consult-if-relevant — do not name the proving test (step 7) without it. If `<mango>` does not
   resolve, say so and still classify every frontend AC above the logic layer rather than dropping the
   check. On `track=backend` it does not apply.
   **Binding gate rule — the layer-match is enforced, not advisory.** If an AC's **risk layer is
   integration / runtime / e2e and its proof artifact is at the logic/unit layer**, that row is a
   layer mismatch → `❌` and **Gate 2 is blocked**. The row passes only when the proof is **upgraded**
   to the matching layer, OR it is recorded as a **named, human-approved coverage-gap exclusion**
   (item · risk tier · why deferred · follow-up · **expiry** · **seen**) in the working doc's
   *Coverage-gap exclusions* slot. A layer-match `❌` that is neither upgraded nor a recorded
   human-approved exclusion **blocks Gate 2 — it does not pass silently.**

   **Every coverage-gap exclusion carries an `expiry:` — debt with a deadline, never a permanent
   waiver.** Reuse the **`expiry:` shape and wording** the learning loop already uses for a type-6
   adjudicated non-defect — do not invent a second vocabulary for the same idea (see
   `<mango>/templates/claim-record.md` `expiry:` and `<mango>/principles/learning-loop.md`):

   `expiry: <ticket key | date | condition that ends this deferral>`

   The value must be **checkable by a reader who is not the author** — a ticket key, a date, or a
   stated condition (`when the anchor index is available`) an outside reader can verify **without
   asking you**. Two failure modes, both blocking:
   - **No `expiry:`** → the exclusion **does not count as recorded**, so the layer-match `❌` it was
     covering **blocks Gate 2** exactly as it would unexcluded.
   - **A present-but-unverifiable `expiry:`** — vague prose an outside reader cannot check (`later`,
     `when appropriate`, `once we get to it`, `soon`) — is **flagged, not accepted**. Presence is not
     checkability: an `expiry:` filled with anything is worth nothing. This is the line the whole field
     turns on — a field that accepts any string re-creates the permanent gap wearing a temporary label.

   **A recurring exclusion class escalates at the third occurrence — reuse the `seen:` recurrence
   ledger.** Track occurrences of the **same exclusion class across tickets** with a `seen:` list — one
   ticket key per prior sighting — the **same shape** the learning loop uses for claim recurrence
   (`<mango>/templates/claim-record.md` `seen:`). Do **not** build a parallel counter. On the **third**
   occurrence of the same class (its `seen:` list already names **two** prior tickets), the exclusion
   **may not simply be recorded again**: it must either be **discharged** (the deferred check now runs,
   or the follow-up landed) **or escalated as a named open item the human answers**. Under `autorun` a
   named open item the human must answer is a clarification — it counts toward `j`, and `j > 0` stops
   the run. **The threshold is three because that is where the evidence sits:** a coverage-gap exclusion
   of one AC class was recorded on three successive tickets and the defect it deferred shipped on the
   third — three is a measurement, not a taste. mango **records and surfaces; the human decides**
   whether an exclusion is discharged — there is no automatic discharge.

   **An overdue predecessor is surfaced, not silently carried.** When this ticket records an exclusion
   whose class already has a **predecessor whose `expiry:` has passed** (a ticket key that merged, a
   date now past, a condition now true) while its follow-up never landed, that fact **appears in the
   counted `EXCLUSIONS:` line below** — it does not add a new artifact, it extends the line that reports
   exclusions.

   **The counted line — emit it on EVERY run, zeros included:**

   `EXCLUSIONS: <n> recorded | <e> with a checkable expiry | <r> recurring (class seen ≥ 3 → discharged/escalated) | <o> with an overdue predecessor`

   `e < n` (an exclusion with no `expiry:` or an unverifiable one), or an `r` that names a
   third-occurrence class **silently re-recorded** instead of discharged or escalated, **blocks Gate 2**
   — as unmissable as an unfilled matrix column. `o > 0` is a **surfacing**: mango reports it; the
   **human** decides whether the overdue exclusion is discharged. `n = 0` closes the line with all zeros
   and adds **no** work: `EXCLUSIONS: 0 recorded | 0 with a checkable expiry | 0 recurring | 0 with an
   overdue predecessor`. **A first exclusion of a class, with a checkable expiry, is legitimate and
   common — accepted with no escalation and no extra step** (`r = 0`); blocking a first, well-formed
   deferral would make every genuinely deferred check a gate failure.
7. **Proving test (at the matching layer).** With the risk layer classified (step 6), name the
   **proving test**: the specific assertion that **fails pre-change and passes post-change**,
   runnable via `config.test_command`, and **sitting at the risk layer** of the AC it proves. State
   the exact invocation. Gate 2 cannot pass without it; a proving test below its AC's risk layer is a
   layer-match `❌` and blocks Gate 2 (see step 6).
8. **Rollback + porting plan.** State how to revert, and the porting plan across `config.repos` if
   the change touches shared code (which repos, in what order).
9. **Confirm SCOPE.** Re-affirm or adjust `SCOPE: S|M|L` from analysis; if it grew, say why. If the
   realized scope has **crossed up a tier** (especially S/M → L) or the change-list materially
   exceeds the analysis baseline, raise the *outgrew-its-ticket* nudge at this gate: stop to
   **re-scope or split** (and flag any branch/PR-type drift) rather than silently absorbing it.
10. **Self-audit, then STOP at Gate 2.** Confirm: the `HANDLES:` line is emitted with `<u> unanswered`
    at `0` and `h == t + x` (every recalled type-2 handle traced with a command + result, or closed with
    `does not apply because <reason>`), every change-list item has a matrix row, `Ph2
    covered by` filled `k/N`, every assumption tagged and every `novel-untested` 3p/runtime one
    resolved (spike result or integration-shaped proving test), proving test named and runnable, the
    verification plan has **no ❌** (or every ❌ is recorded as a human-approved coverage-gap
    exclusion carrying a **checkable `expiry:`** and a follow-up), the **`EXCLUSIONS:` counted line**
    emitted with `e == n`, every third-occurrence class discharged or escalated (never silently
    re-recorded) and any overdue predecessor surfaced, rollback + porting recorded, and — when track
    includes frontend —
    `DESIGN.md` created/updated (per `<mango>/skills/design/frontend.md`) and, for any universal/app-wide frontend requirement,
    the proof manifest laid out **one row per (AC × surface)** with `N == M + X` (no under-coverage
    banner standing). Write Phase 2 into the working doc and update `Session status`, then STOP and
    wait for the user. Do not begin execution.
