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

## Steps

1. **Run the `reviewer` agent** on the working-tree diff. It reads `config.rulebook_path` /
   `config.standards_path` and returns a verdict (BLOCK / CHANGES REQUESTED / LGTM) plus findings.
2. **Run the `challenger` agent ticket-blind.** Give it ONLY the ticket key/raw text and the
   diff/branch — **NOT** the working doc, design, or rationale. It rebuilds the requirements from
   the raw ticket and judges each met / not met / can't tell with `path:line`.
3. **Optional project security agent.** If the project defines one, run it on the diff.
4. **Reconcile scope vs the approved list.** Any file outside the Gate-2 list, or reformatting of
   untouched lines, is **not clean**.
5. **Regression check.** Re-check the Phase-1 callers / blast radius for regressions.
6. **Proving test.** Run it via `config.test_command`. Record the result and answer: **"would it
   fail without the change?"**
7. **Fill `Ph3/4 proven by`** (`k/N`) for every matrix row and universal-inventory item.
8. **Decide clean vs not clean.** Clean requires ALL of:
   - reviewer reports no Critical;
   - challenger finds every item met;
   - `k = N` (or every exclusion is human-approved and recorded);
   - proving test green.
   **Not clean → loop back to the relevant phase and STOP.** Clean → write Phase 4 into the working
   doc, update `Session status`, and proceed to finalise.
