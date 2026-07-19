---
name: review
description: Phase 4 of the mango ticket lifecycle. Use after execute. Runs the reviewer agent on the diff and the challenger agent ticket-blind, reconciles scope vs the approved list, checks the proving test, and fills Ph3/4 proven by. Stops only if the work is not clean.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This phase enforces principle 3 (Surgical
changes) via the scope reconciliation and principle 4 (Goal-driven) via the proving-test result and
the `k/N` denominator.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`.

**Model delegation** (see `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`): the review verdict and the
challenger's requirement reconstruction are the **highest-judgment** step — run them on Sonnet, and
**never** on Haiku. The Haiku `extractor` worker may only gather context for you (e.g. pull caller
snippets); it never produces a verdict.

**Reviewer selection (concrete, not advisory).** A skill cannot re-pin a subagent's model at
runtime, so the Opus upgrade is a **choice of agent**, not a setting:
- Dispatch **`reviewer-max`** (Opus) when `config.cost_tier == "max"` **AND** the diff is
  high-stakes — the ticket is security-tagged, **or** the diff touches auth / access control / data
  access / schema-migration per `config.rulebook_path`.
- Otherwise dispatch **`reviewer`** (Sonnet).
- **Never** dispatch a Haiku reviewer.

## Git isolation (binding) — subagents inspect refs, never mutate the shared working tree

Both the `reviewer` and the `challenger` inspect the diff/branch **read-only and ref-based** —
`git diff <base>..<branch>`, `git show <branch>:<path>`, `git log <base>..<branch>` — or in an
**isolated `git worktree`** (`git worktree add <scratch> <branch>`, removed afterward). A review
subagent **MUST NOT** run `git checkout`, `git switch`, `git stash`, or any HEAD/index-mutating git in
the **shared working tree (the live checkout)**: that switches the main worktree off the in-progress
feature branch onto another ref, strips the in-progress source files from disk, and leaves the working
doc untracked — a real corruption. If a subagent needs to **run** the suite against the branch (not
just read it), it uses an **isolated `git worktree` / clone**, exactly as v1.6.1's eval isolation does —
never the live checkout. This is stated once in `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` (Subagent git
isolation) — same root cause as the eval-path fix, now applied to the review surface — and is guarded by
`scripts/validate.py`.

## Steps

1. **Run the reviewer agent** on the working-tree diff — `reviewer` or `reviewer-max` per the
   **Reviewer selection** rule above. It reads `config.rulebook_path` / `config.standards_path` and
   returns a verdict (BLOCK / CHANGES REQUESTED / LGTM) plus findings. **When TRACK (from analysis)
   includes frontend, inject `${CLAUDE_PLUGIN_ROOT}/templates/frontend-rubric.md` into the reviewer's
   brief** (and the challenger's) so it also scores the frontend rubric — see the **Frontend track**
   section below. Do **not** fork the agents per track; the rubric is injected content.
2. **Run the `challenger` agent ticket-blind.** **Construct its input explicitly** so independence
   is procedural, not just requested: build the payload as exactly *(a)* the **raw ticket portion
   only** plus *(b)* the diff/branch. Source the raw ticket by `config.work_doc_mode`:
   - **separate working doc** (tracker-hosted, or `work_doc_mode: separate`) → re-fetch the raw ticket
     **from the tracker** (`config.tracker.read_mcp`, or have the user paste it) — do NOT copy it out
     of the working doc — and **exclude** `<config.work_dir>/<KEY>.work.md` entirely.
   - **embedded working doc** (local-file ticket under `auto`/`embed`) → take **only the text above
     the raw-ticket separator line** in the ticket file; **exclude everything below the separator**
     (the appended working doc — design, matrix, rationale).
   In both modes the payload **excludes the working-doc portion** (design, matrix, rationale). Invoke
   the challenger as a fresh subagent with only that payload — **never** the working-doc portion. It
   rebuilds the requirements from the raw ticket and judges each met / not met / can't tell with
   `path:line`. This is a procedural guarantee backed by the path/separator separation (the
   orchestrator withholds the working doc and re-derives from the raw ticket), not a cryptographic
   one — state that honestly if asked.
3. **Optional project security agent.** If the project defines one, run it on the diff.
4. **Reconcile scope vs the approved list — on BOTH axes.** Scope discipline is measured on the
   **file set** AND on **conformance to the approved design behaviour** — a clean file diff does not
   certify behavioural conformance.
   - **File axis.** Any file outside the Gate-2 list, or reformatting of untouched lines — including
     a **wholesale reformat of a shared or pre-existing file** by a formatter run beyond the
     authored/edited files (the execute **format-scope rule**) — is **not clean**.
   - **Behaviour axis.** Re-read the Gate-2 **Approach** bullets against what execute actually
     implemented. Any bullet implemented **differently** from the approved design is a **behavioural
     deviation** and must be adjudicated here — **even when the file diff is a clean subset of the
     approved list** (`diff ⊆ list ✅`). A deviation execute recorded (its Phase-3 design-conformance
     self-check) is surfaced for your decision; a deviation execute **missed** — a bullet you find
     diverged, or a feature self-marked `✅` that was not actually implemented — is a review finding
     and is **not clean**.
5. **Regression check.** Re-check the Phase-1 callers / blast radius for regressions.
6. **Proving test — judged against the recorded baseline, not "all green".** Run it via
   `config.test_command`. Record the result and answer: **"would it fail without the change?"**
   Compare the run against the `BASELINE:` recorded at analysis, **not** against a blanket "all
   green". When `baseline: red | flaky`, the bar is **delta-green**: the change must have introduced
   **no new failure** and must have fixed any it claimed to; a pre-existing failure that remains
   **outside** the change is a **recorded baseline exclusion** — it does **not** block clean, and it
   is **not** a silent pass (it is named). A **new** failure the change introduced, or a claimed fix
   that did not land, blocks clean.
7. **Fill `Ph3/4 proven by`** (`k/N`) for every matrix row and universal-inventory item. For a
   counted **"for each of N"** requirement, verify **item-by-item** and fill the **per-item** rows of
   its inventory checklist — the gate is not clean until **every** item is confirmed (or each
   unconfirmed item is a recorded, human-approved coverage-gap exclusion). An aggregate "k/N" alone
   is **insufficient** for a "for each" requirement: a passing total can hide an incomplete tail.
8. **Layer-match re-confirmation (binding).** Re-confirm that **no AC closed clean on a
   layer-mismatched proof.** Walk design's verification plan: any row whose proof artifact sits below
   its risk layer (a layer-match `❌`) that is **not** a recorded, human-approved coverage-gap
   exclusion **blocks clean** — the proof must be upgraded to its risk layer, or the gap recorded as
   a human-approved exclusion. A green proving test at the wrong layer is not coverage.
9. **Decide clean vs not clean.** Clean requires ALL of:
   - reviewer reports no Critical;
   - challenger finds every item met — **except** a challenger "not met" that corresponds to a
     **recorded, human-approved coverage-gap exclusion** (from design's verification plan / the
     working doc's *Coverage-gap exclusions* slot) does **not** block clean: it is a known proof-tier
     mismatch, not an unmet requirement. An *unrecorded* gap still blocks.
   - no layer-match `❌` stands unresolved (step 8);
   - `k = N` (or every exclusion is human-approved and recorded);
   - **surface coverage `N == M + X`** for every universal/app-wide frontend requirement (the
     proof-manifest check below) — any `M + X < N` blocks with a visible `surfaces proven: <M+X>/<N>`;
   - proving test green.
   **Not clean → loop back to the relevant phase and STOP.** Clean → record the **stale-review
   guard** marker `Reviewed at <commit SHA>` plus the set of reviewed files in the working doc (step
   10), write Phase 4, update `Session status`, and proceed to finalise.
10. **Record the reviewed commit (stale-review guard).** On a clean verdict, capture the exact
    `HEAD` SHA and the set of files the review covered, and write a `Reviewed at <sha>` marker (with
    the reviewed-file list **and the working-doc path** — the separate `<config.work_dir>/<KEY>.work.md`
    or the embedded local-ticket file per `config.work_doc_mode`) into the working doc's Phase-4 slot.
    Recording the working-doc path makes `finalise`'s exemption unambiguous — that path (and any mango
    bookkeeping file) is excluded from the staleness comparison. A clean review is scoped to that
    commit: `finalise` compares the live tree against this marker and **refuses** to open a PR if any
    non-exempt file changed **beyond the reviewed set**, routing back here for a re-review (see
    `finalise`).

## Re-review after CHANGES REQUESTED — conditional LGTM + verify-only pass

A round-1 `CHANGES REQUESTED` need not cost a full second dispatch when round 2 is pure
re-confirmation. Two options, chosen by the reviewer:

- **Conditional LGTM.** Round 1 may return a **conditional LGTM** — *"LGTM once findings 1–N land as
  described"* — naming exactly the N findings that must be fixed and how. This is the reviewer's
  signal that nothing else is outstanding.
- **Verify-only re-review — main-loop by default (no re-dispatch).** When round 1 was a conditional
  LGTM and the fixes stay **inside the already-named findings**, the re-review is a **verify-only pass
  done in the main loop, dispatching no subagent**: confirm the N named fixes are present **as
  described** by inspection, re-run **only the affected proof**, and run a **regression scan** over the
  Phase-1 callers / blast radius — **without** a full requirement re-derivation. This is the **explicit
  default**, not operator taste: an in-scope verify-only round does **not** re-dispatch a reviewer or a
  challenger, so its cost does not swing on whoever ran it. A reviewer / challenger is **re-dispatched
  only when a fix changed scope** — it touched a file outside the approved set, or introduced a new
  surface/behaviour beyond the named findings — and that is the **only** trigger for re-dispatch; a
  scope-changing fix reverts the round to a **full re-review**. The ticket-blind **`challenger`'s full
  re-derivation runs once** (round 1); its independence is the value, so it is **not repeated** on a
  verify-only round **unless a fix changed scope**. The verify-only path is an option, never a shortcut
  that skips a real re-check: if it finds a named fix missing or a regression, it escalates back to a
  full review.

  **Docs/bookkeeping carve-out (a file outside the approved set is not always a scope change).** The
  re-dispatch trigger reuses `finalise`'s **staleness exemption set** — the working doc, `config.lessons_path`,
  and the rule-book **drift-list** section (`codify`'s tech-debt list) — pure **bookkeeping** files with
  **zero runtime surface**. A verify-only fix that touches **only** these **exempt** bookkeeping files
  stays **main-loop** (verify by inspection + re-run only the affected proof + the regression scan) and
  does **not** trigger a full re-dispatch — recording a durable lesson or updating the drift list is not
  a scope change. A fix touching **any non-exempt** file outside the approved set (product source, a
  test, config, a new surface/behaviour) still **changes scope** and reverts the round to a full,
  re-dispatched re-review. The carve-out narrows the trigger to exempt bookkeeping only; it never widens
  what a real scope change is.

  **The cheap path is the default, not luck (main-loop + scope the re-run — do not re-do round 1).** A
  verify-only round runs **in the main loop** and must **carry forward round-1's verified facts** (the
  requirement reconstruction, the passing proving test, the layer-match verdicts, the baseline) and
  **re-run only the proof affected by the named fixes** plus the regression scan. It must **not
  re-dispatch a subagent**, **not re-derive requirements**, and **not blanket-re-run the full build /
  lint / tsc / test suite or re-read the files from scratch** — **unless a named fix changed scope**
  (touched a file or behaviour beyond the findings), the one condition that reverts it to a full,
  re-dispatched re-review. Reuse what round 1 already established; re-prove only what the fixes actually
  changed. This is what makes the verify-only round **consistently cheaper** than the full round — the
  cost is pinned by the main-loop-default, not left to a coin flip that can cost *more* by re-dispatching
  and re-running everything.

Everything else (clean-decision criteria, the stale-review marker) is unchanged: a verify-only pass
that confirms all N fixes + a clean regression scan yields a clean verdict and records the
`Reviewed at <sha>` marker exactly as a full review would.

## Frontend track — score the rubric against `DESIGN.md` (only when `config.track` includes frontend)

When TRACK includes frontend, the reviewer **and** the challenger also score
`${CLAUDE_PLUGIN_ROOT}/templates/frontend-rubric.md`. Every rubric item is **falsifiable**
(measurable or greppable) and is checked **against the project's `DESIGN.md`**
(`config.design_doc_path`), never against a blanket aesthetic rule — "is it tasteful?" is **out** of
the rubric; taste exists only as `DESIGN.md` conformance. The rubric covers:

- **Core (always):** matches `DESIGN.md` (colour/font/spacing/radius from agreed tokens); no
  hardcoded hex/px outside tokens (grep); semantic HTML; **state never by colour alone** (icon +
  text); `prefers-reduced-motion` respected; no aesthetic change mixed into a logic/backend PR.
- **Responsive & touch — M1–M10 (all falsifiable):** viewport meta / zoom (M1), no horizontal scroll
  at each breakpoint + the 320 px floor (M2), reflow @320 px (M3), **touch-target** ≥ 44×44 px with
  ≥ 8 px spacing (M4), input zoom guard ≥ 16 px (M5), tap/hover parity (M6), focus-visible + ≥ 3:1
  indicator (M7), contrast (M8), safe-area respect (M9), pointer-input parity (M10). These are the
  **a11y** / responsive gates; each carries its risk layer for the layer-match gate.

**Layer-match re-confirmation extends to the frontend ACs (do not fork it).** Each M-gate carries a
risk layer above the logic/unit layer (`document` / `computed-style` / `integration/runtime` /
`behavioral`); a unit-only proof (mocked DOM) clears **none** of them. Re-confirm at step 8 that no
frontend AC closed clean on a layer-mismatched proof — a `❌` blocks clean unless it is a recorded,
human-approved coverage-gap exclusion.

**M10 degrades gracefully — it never wedges the review.** Its always-on greppable smell (a mouse-only
handler or hover-only interaction with no pointer/touch equivalent) always runs and can block; its
best-effort behavioral dispatch-assert runs **only when the environment can**, and when it can't it
is recorded as a named human-approved coverage-gap exclusion rather than blocking.

## Surface-coverage proof manifest — the `N == M + X` check (frontend universal/app-wide reqs)

For each universal / app-wide frontend requirement, the challenger scores the **proof-manifest**
(`execute`'s one-row-per-(AC × surface) record) — independently of the working doc, preserving its
ticket-blindness: it **re-enumerates the reachable surfaces from the branch code** (this is its own
`SURFACES` count) and rebuilds the requirement from the raw ticket, then checks every reachable
surface has a proof in the diff. The count:

- `N` = |reachable surfaces from code| · `M` = surfaces with a valid **PASS (any tier)** · `X` =
  recorded human-approved **EXCLUDED**. **The gate passes iff `N == M + X`.** A ticket-scoped proof
  covering 2 of 5 reachable surfaces yields `N=5, M=2` → **blocked**, with the loud banner
  `⚠ surfaces proven: 2/5 — <uncovered> have no proof; cover or record an exclusion.`
- **Score each entry by tier:** a `PASS(automated)` row against the **C1–C8** automated-proof contract
  (real SUT not mocked, threshold asserted not "looks ok", role+name selectors — a non-role selector
  with no recorded reason is flagged, one layer per AC, determinism); a `PASS(render@<bp>)` row against
  the lighter **render-proof contract** (real surface at the breakpoint, visible measurable asserted,
  a recorded artifact the reviewer can see). A `render@<bp>` is a **first-class proof, not an
  exclusion** — do not demand a runner where the project has none.
- **Defeat fabricated entries:** the challenger **re-runs ≥ 1** tier-1 `proof-cmd` (or, for tier-2,
  **confirms the recorded render artifact exists**). Under **`TIER=lite`** this lightens to
  **confirming command/artifact presence** rather than a live re-run — but surface coverage, the
  manifest, and a proof per surface stay **mandatory**.

This **extends** the step-8 layer-match re-confirmation; it does not fork it. `fullstack` applies this
to its frontend ACs only; a `track=backend` ticket has no manifest and this section is inert.
