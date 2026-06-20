# <KEY> — <ticket title>

- **Ticket:** <KEY> · <tracker link>
- **Type:** bug | enhancement
- **Repo(s) / Porting:** <which config.repos are touched; porting order if shared>
- **SCOPE:** S | M | L

---

## Requirements matrix

`SECTIONS: <n> found (names) | <n> decomposed | ROWS: C=.. R=.. G=.. AC=..`

| ID | Source | Verbatim | Interpretation | Ph1 evidence | Ph2 covered by | Ph3/4 proven by | Status |
|----|--------|----------|----------------|--------------|----------------|-----------------|--------|
| C1 |        |          |                |              | k/N            | k/N             | ✅/⚠/❌ |
| R1 |        |          |                |              | k/N            | k/N             | ✅/⚠/❌ |
| G1 |        |          |                |              | k/N            | k/N             | ✅/⚠/❌ |
| AC1|        |          |                |              | k/N            | k/N             | ✅/⚠/❌ |

Status legend: ✅ done/proven · ⚠ deferred (needs follow-up ticket) · ❌ not met.

## AC validation

Independently re-derive every concrete acceptance value. A mismatch is a Gate-1 question carrying
the computed value — never a silent correction.

| AC ID | Ticket states | Independently computed | Match? | If mismatch → Gate-1 question |
|-------|---------------|------------------------|--------|-------------------------------|
|       |               |                        | Y/N    |                               |

## Inventory (universal "all/every/no" requirements)

- **Denominator / total N:** <N>
- Numbered list of every affected item:
  1.
  2.

## Clarifications

`CLARIFICATION: <M> raised | <k> self-resolved (cited) | <j> for human decision`

- Self-resolved (with citation: rulebook §, `path:line`, or ticket line):
- For human decision (**if any, STOP at Gate 0**):

---

## Phase 1 — Analysis ✋ Gate 1

- Root cause (bug, classified vs cause_taxonomy) **or** per-goal gap analysis (enhancement), with `path:line`:
- Handler / entry point + blast radius (callers, dependents):
- Self-audit:
- **Gate 1 status:** waiting on user / cleared

## Phase 2 — Design ✋ Gate 2

- Approach:
- Rejected alternatives:
- Smallest change-list (every item traces to a matrix row): see matrix `Ph2 covered by`.
- Rule compliance (vs rulebook_path / standards_path):
- **Proving test** (fails pre-change, passes post-change; invocation via test_command):
- Rollback + porting plan across repos:
- SCOPE confirmed:
- **Gate 2 status:** waiting on user / cleared

## Phase 3 — Execute

- Branch:
- Commits (logical units; no AI co-author trailer):
- Proving test added:
- **Verification sweep:** zero stray references ✅/❌ · diff ⊆ approved list ✅/❌ · each hunk maps to a row ✅/❌

## Phase 4 — Review ✋ (stop only if not clean)

- reviewer verdict (BLOCK / CHANGES REQUESTED / LGTM):
- challenger (ticket-blind) result:
- security agent (if any):
- Scope reconciliation (files outside list / reformatting):
- Regression on Phase-1 callers:
- Proving test result + "would it fail without the change?":
- `Ph3/4 proven by` filled (k/N): see matrix.
- **Clean?** reviewer no Critical AND challenger every item met AND k=N (or exclusions approved) AND proving test green → yes/no

## Phase 5 — Finalise ✋ final gate

- PR draft: `/tmp/pr-<KEY>.md`
- Planned outward actions (each needs separate approval):
  - [ ] push branch
  - [ ] open PR via pr_host
  - [ ] tracker comment (via tracker.cli)
  - [ ] tracker transition (via tracker.cli)
- Follow-up tickets drafted for deferred (⚠) rows:
- Revert path:

---

## Decision log

| When | Decision | Why |
|------|----------|-----|
|      |          |     |

## Session status

- **Last updated:**
- **Current phase:**
- **Next action:** <concrete; never "continue">
- **Blocked on:**
