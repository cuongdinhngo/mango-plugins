---
name: design
description: Phase 2 of the mango ticket lifecycle. Use after analysis clears Gate 1. Produces the approach, rejected alternatives, the smallest change-list traced to matrix rows, rule-compliance check, and the named proving test. Stops at Gate 2.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This phase enforces principle 2 (Simplicity
first) via the smallest change list + `SCOPE`, and principle 4 (Goal-driven) via the named proving
test required at this gate.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path` and `config.standards_path`. If `.harness.json` is missing, STOP and tell the
user to create one from `${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. No code is written in
this phase.

## Steps

1. **Confirm Gate 1 cleared.** Read `<config.tickets_dir>/<KEY>.md`. The requirements matrix and AC
   table must be filled and `CLARIFICATION` `j = 0`. If not, return to analysis.
2. **Approach + Rejected alternatives.** State the chosen approach in a few lines, then record at
   least one **Rejected alternative** and why (enforces principle 1's record of thought).
3. **Smallest change-list table.** List the minimum set of changes. Columns: change, file/area,
   `Ph2 covered by` (which matrix row(s)), `k/N`. **Every item must trace to a matrix row** — an
   item with no row behind it fails the gate. Prefer the smallest edit; no speculative abstraction,
   no indirection serving a single call site.
4. **Rule compliance.** Check the proposed change against `config.rulebook_path` and
   `config.standards_path`; note any rule that constrains the design and how you comply.
5. **Proving test.** Name the **proving test**: the specific assertion that **fails pre-change and
   passes post-change**, runnable via `config.test_command`. State the exact invocation. Gate 2
   cannot pass without it.
6. **Rollback + porting plan.** State how to revert, and the porting plan across `config.repos` if
   the change touches shared code (which repos, in what order).
7. **Confirm SCOPE.** Re-affirm or adjust `SCOPE: S|M|L` from analysis; if it grew, say why.
8. **Self-audit, then STOP at Gate 2.** Confirm: every change-list item has a matrix row, `Ph2
   covered by` filled `k/N`, proving test named and runnable, rollback + porting recorded. Write
   Phase 2 into the working doc and update `Session status`, then STOP and wait for the user. Do not
   begin execution.
