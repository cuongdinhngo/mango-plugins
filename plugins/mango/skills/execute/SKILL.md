---
name: execute
description: Phase 3 of the mango ticket lifecycle. Use after design clears Gate 2. Implements ONLY the approved change list on a fresh branch, adds the proving test, runs a verification sweep proving the diff is a subset of the approved list, then flows straight to review. Autonomous (no gate).
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This phase enforces principle 3 (Surgical
changes) via the verification sweep and the diff ⊆ approved-list check.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. This phase is autonomous — it does not stop at
a gate — but it implements ONLY what Gate 2 approved.

**Model delegation** (see `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`): implementing the approved change
list and drafting the PR body are **execute** work — Sonnet. Bulk read-and-extract may go to the
Haiku `extractor` worker. Run the verification sweep's grep / tests / lint via the Bash tool
directly — never spawn a model for a one-line shell command.

## Steps

1. **Confirm Gate 2 cleared.** Read `<config.tickets_dir>/<KEY>.md`: approved change list, proving
   test, and `SCOPE` must be present. If not, return to design.
2. **Branch.** Create a branch per `config.branch_strategy` (default `fix|feat|chore/<KEY>-<slug>`)
   in the target repo's `config.repos[].root`. One branch for the approved work.
3. **Implement the approved change list — and only it.**
   - Make exactly the changes in the Gate-2 list; nothing more.
   - Match surrounding style.
   - **Never reformat lines you are not changing.**
   - Remove only orphans your change itself created; do not delete pre-existing dead code.
4. **Add the proving test** named at Gate 2. Confirm it fails on the pre-change state if you can,
   then passes after the change.
5. **Verification sweep.** Prove:
   - zero stray references introduced (no dangling symbols/imports from the edit);
   - the diff ⊆ approved change list (no file outside the list, no untouched-line reformatting);
   - each diff hunk maps to a matrix row.
   Record the sweep result in the working doc.
6. **Commit per logical unit.** One commit per logical unit, clear messages, **no AI co-author
   trailer of any kind**.
7. **Write back + flow to review.** Write Phase 3 into the working doc (including the sweep result
   and `Ph3/4 proven by` progress), update `Session status`, then flow straight into the `review`
   phase. Do not perform any outward action (no push, no PR, no tracker write).
