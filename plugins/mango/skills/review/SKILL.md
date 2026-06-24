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

## Steps

1. **Run the reviewer agent** on the working-tree diff — `reviewer` or `reviewer-max` per the
   **Reviewer selection** rule above. It reads `config.rulebook_path` / `config.standards_path` and
   returns a verdict (BLOCK / CHANGES REQUESTED / LGTM) plus findings.
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
4. **Reconcile scope vs the approved list.** Any file outside the Gate-2 list, or reformatting of
   untouched lines, is **not clean**.
5. **Regression check.** Re-check the Phase-1 callers / blast radius for regressions.
6. **Proving test.** Run it via `config.test_command`. Record the result and answer: **"would it
   fail without the change?"**
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
   - proving test green.
   **Not clean → loop back to the relevant phase and STOP.** Clean → record the **stale-review
   guard** marker `Reviewed at <commit SHA>` plus the set of reviewed files in the working doc (step
   10), write Phase 4, update `Session status`, and proceed to finalise.
10. **Record the reviewed commit (stale-review guard).** On a clean verdict, capture the exact
    `HEAD` SHA and the set of files the review covered, and write a `Reviewed at <sha>` marker (with
    the reviewed-file list) into the working doc's Phase-4 slot. A clean review is scoped to that
    commit: `finalise` compares the live tree against this marker and **refuses** to open a PR if the
    diff moved beyond it, routing back here for a re-review (see `finalise`).
