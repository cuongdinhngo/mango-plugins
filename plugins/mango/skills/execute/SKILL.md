---
name: execute
description: Phase 3 of the mango ticket lifecycle. Use after design clears Gate 2. Implements ONLY the approved change list on a fresh branch, adds the proving test, runs a verification sweep proving the diff is a subset of the approved list, then flows straight to review. Autonomous (no gate).
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This phase enforces principle 3 (Surgical
changes) via the verification sweep and the diff ⊆ approved-list check.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. This phase is autonomous — it does not stop at
a gate — but it implements ONLY what Gate 2 approved. Autonomy is **not** licence to thrash or to
barrel on with a broken approach: the two STOP conditions in **Escalations** below are mandatory.

**Model delegation** (see `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`): implementing the approved change
list and drafting the PR body are **execute** work — Sonnet. Bulk read-and-extract may go to the
Haiku `extractor` worker. Run the verification sweep's grep / tests / lint via the Bash tool
directly — never spawn a model for a one-line shell command.

## Steps

1. **Confirm Gate 2 cleared.** Read the working doc `<config.work_dir>/<KEY>.work.md`: approved
   change list, proving test, and `SCOPE` must be present. If not, return to design.
2. **Branch.** Create a branch per `config.branch_strategy` (default `fix|feat|chore/<KEY>-<slug>`)
   in the target repo's `config.repos[].root`. One branch for the approved work.
3. **Implement the approved change list — and only it.**
   - Make exactly the changes in the Gate-2 list; nothing more.
   - Match surrounding style.
   - **Never reformat lines you are not changing.**
   - Remove only orphans your change itself created; do not delete pre-existing dead code.
4. **Add the proving test** named at Gate 2. Confirm it fails on the pre-change state if you can,
   then passes after the change. If it keeps failing, the two **Escalations** below apply — do not
   loop indefinitely and do not silently swap in a different approach.
5. **Verification sweep.** Prove:
   - zero stray references introduced (no dangling symbols/imports from the edit);
   - the diff ⊆ approved change list (no file outside the list, no untouched-line reformatting);
   - each diff hunk maps to a matrix row.
   Record the sweep result in the working doc. If the realized diff **materially exceeds** the
   approved change list or the declared `SCOPE` has crossed up a tier (S/M → L), do not absorb it —
   surface the *outgrew-its-ticket* nudge at the next gate (review) so the human can re-scope or
   split, and flag any branch/PR-type drift.
6. **Commit per logical unit.** One commit per logical unit, clear messages, **no AI co-author
   trailer of any kind**.
7. **Write back + flow to review.** Write Phase 3 into the working doc (including the sweep result
   and `Ph3/4 proven by` progress), update `Session status`, then flow straight into the `review`
   phase. Do not perform any outward action (no push, no PR, no tracker write).

## Escalations (mandatory STOP conditions)

These interrupt the autonomous flow. Both record the finding in the working doc before stopping.

- **Design invalidated → re-gate.** Trigger: a test (or the proving test itself) reveals the
  approved **Gate-2 approach cannot work as designed** — not a bug in your edit, but the design's
  premise being false. Action: **STOP execute. Do NOT silently invent a replacement approach and do
  NOT continue with a known-broken one.** Record the finding (with `path:line` / the test signature)
  in the working doc's Phase-3 *Design-invalidation* slot, surface the options to the user, and
  **re-open Gate 2** with a revised approach — which must re-pass design's **Assumptions** check and
  **verification plan** (A + B). (Observed failure: execute discovered a Gate-2 "reuse the per-tab
  mounting for two panes" design was unworkable; mango had no defined transition, so the operator
  had to improvise stop → ask → re-approve.)
- **Stuck-detector / circuit-breaker.** After **K** failed attempts against the **same** proving
  artifact / same failing-test signature (default `K=3`, configurable as `config.stuck_threshold`
  in `.harness.json`), **STOP and escalate to the user** with a summary of what was tried and the
  options — instead of continuing. The counter **resets when the failing signature changes** (a new
  error means real progress). (Observed failure: ~7 attempts ran against the same failing e2e before
  anyone escalated; nothing bounded repeated attempts at one proof.)
