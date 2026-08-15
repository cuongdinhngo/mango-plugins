---
name: review
description: Phase 4 of the mango ticket lifecycle. Use after execute. Runs the reviewer agent on the diff and the challenger agent ticket-blind, reconciles scope vs the approved list, checks the proving test, and fills Ph3/4 proven by. Stops only if the work is not clean.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This phase enforces principle 3 (Surgical
changes) via the scope reconciliation and principle 4 (Goal-driven) via the proving-test result and
the `k/N` denominator.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`<mango>/config/harness.example.json`.

**Model delegation** (see `<mango>/PRINCIPLES.md`): the review verdict and the
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

**READ `<mango>/principles/git-isolation.md` NOW, before dispatching any review subagent.** It is the
binding contract this section applies; the read is unconditional, not consult-if-relevant. If `<mango>`
does not resolve, say so and enforce at minimum the rules restated below — never skip the section.

Both the `reviewer` and the `challenger` inspect the diff/branch **read-only and ref-based** —
`git diff <base>..<branch>`, `git show <branch>:<path>`, `git log <base>..<branch>` — or in an
**isolated `git worktree`** (`git worktree add <scratch> <branch>`, removed afterward). A review
subagent **MUST NOT** run `git checkout`, `git switch`, `git stash`, or any HEAD/index-mutating git in
the **shared working tree (the live checkout)**: that switches the main worktree off the in-progress
feature branch onto another ref, strips the in-progress source files from disk, and leaves the working
doc untracked — a real corruption. If a subagent needs to **run** the suite against the branch (not
just read it), it uses an **isolated `git worktree` / clone**, never the live checkout. This is stated
once in `<mango>/PRINCIPLES.md` (Subagent git isolation) and is guarded by
`scripts/validate.py`.

### Worktree ≠ environment-equivalence (binding — carry the untracked env, or run in place)

A fresh `git worktree` contains only **tracked** files. It therefore has **none** of the project's
required **untracked** environment — `.env` / local config, local certs, installed dependencies, built
assets — so the app cannot boot and **every** test fails for an environmental reason that has nothing to
do with the diff. Two allowed paths, in order of preference:

1. **Run read-only in place** when the working tree is **already at the reviewed SHA** (nothing to
   check out, nothing to switch): the cheaper and safer path. Read-only means run the suite; still no
   `checkout`/`switch`/`stash`.
2. **Carry the required untracked environment into the run-worktree** — at minimum the `.env` / local
   config the app needs to boot, plus whatever the project's setup step installs — **before** running
   the suite. Copy it in; never commit it, and never write a secret into a tracked file.

**Sanity rule — a near-total failure inside a fresh worktree is an ENVIRONMENT FAULT, not a finding.**
If a suite run inside a fresh worktree fails **near-totally** (all or almost all test files failing,
boot/import/connection errors, a count wildly worse than the recorded `BASELINE:`), treat it as an
**env-fault caused by missing untracked files** **until proven otherwise** — fix the environment parity
and re-run. It **MUST NOT** be reported as a review finding, and it **must not** be recorded as a
regression: a near-total fail is almost never a real regression and almost always a missing `.env`. This
**reclassifies an environment artifact only** — it never suppresses a real finding: a *partial*,
*targeted* failure inside the change's blast radius is still a genuine finding, and once environment
parity is established the same near-total result **is** reportable.

**Empty-diff fallback (put it in every review brief).** `execute` **commits the change-set before
dispatching review**, so a real committed diff exists for the ref-based inspection. If a
`<base>..<branch>` diff nonetheless comes back **empty**, the change may be **uncommitted** — the brief
you hand each subagent must say: *fall back to `git diff HEAD` + `git status --porcelain -uall` before
concluding "no changes"*. An empty range is a reason to look harder, never a no-change verdict.

## Steps

1. **Run the reviewer agent** on the working-tree diff — `reviewer` or `reviewer-max` per the
   **Reviewer selection** rule above. It reads `config.rulebook_path` / `config.standards_path` and
   returns a verdict (BLOCK / CHANGES REQUESTED / LGTM) plus findings. **When TRACK (from analysis)
   includes frontend, inject `<mango>/templates/frontend-rubric.md` into the reviewer's
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

## Frontend track (only when `config.track` includes frontend)

When TRACK includes frontend, **READ `<mango>/skills/review/frontend.md` **and** `<mango>/principles/frontend-track.md` NOW** — before dispatching the
reviewer / challenger — and apply every rule in it: the falsifiable rubric scored against the project's
`DESIGN.md`, the Core plus M1–M10 **a11y** / responsive / **touch-target** items, the frontend
layer-match re-confirmation, M10's graceful degradation, and the surface-coverage **proof manifest**
`N == M + X` check with its `surfaces proven: <M+X>/<N>` banner. This is a **mandatory read**, not a
consult-if-relevant: the rubric it carries is what the reviewer is scored on. If `<mango>` does not
resolve, say so and score at minimum the Core items plus M2/M3/M4/M7/M8 by name rather than dropping
the rubric. On `track=backend` there is no manifest and this section is inert.
