# PRINCIPLES.md — the binding contract

**A principle stated as prose does not bind; an emitted, counted artifact that blocks a gate
does.** Every mango skill references this file. A phase may not pass its gate until the artifacts
named below exist, are filled, and pass their own count/match checks. Silence is never approval.

The four principles follow. Each lists its **Operating rule**, where it is **Enforced at**, and
exactly when it **Fails the gate**.

---

## 1. Think before coding

**Operating rule.** Understand the ticket completely before proposing any change. Every section is
decomposed; every concrete acceptance value is independently re-derived; every ambiguity is raised,
not guessed.

**Enforced at** (analysis → Gate 1):
- The `CLARIFICATION: <M> raised | <k> self-resolved (cited) | <j> for human decision` tally.
  If `j > 0`, STOP at Gate 0 — do not proceed.
- The `AC validation` table: every concrete acceptance value is recomputed independently. A
  mismatch becomes a Gate-1 question carrying the computed value — **never a silent correction**.
- `SECTIONS: <n> found = <n> decomposed`. Every ticket section maps to ≥1 matrix row.
- A `Rejected alternatives` line at design records what was considered and dropped.

**Fails the gate when** a gate is reached with `j > 0` unresolved, an AC mismatch was silently
changed instead of raised, or sections found ≠ sections decomposed.

> **Challenger independence is procedural, not structural.** The `challenger`'s "ticket-blind"
> property holds only because the orchestrator withholds the working doc and re-fetches the raw
> ticket to build its input — not because anything structurally prevents a leak. Treat it as a
> discipline to uphold, and state the limit honestly rather than overclaiming guaranteed independence.

---

## 2. Simplicity first

**Operating rule.** Build the smallest thing that satisfies the requirements. No speculative
abstraction; no indirection that serves a single call site.

**Enforced at** (design → Gate 2; review → Gate 4):
- The **smallest change-list** table plus a declared `SCOPE: S|M|L`.
- Every change-list item traces to a matrix row (the `Ph2 covered by` column, `k/N`).
- The `reviewer` agent flags speculative abstraction and single-use indirection.

**Fails the gate when** a change-list item has no matrix row behind it, or an introduced
abstraction serves only one call site.

---

## 3. Surgical changes

**Operating rule.** Touch only what the approved change list requires. Match surrounding style.
Never reformat lines you are not changing. Never delete pre-existing dead code without instruction.

**Enforced at** (execute → Phase 3; review → Gate 4):
- The **verification sweep**: proves zero stray references and that the diff ⊆ approved list.
- The diff ⊆ approved-list check and the "no reformatting untouched lines" review check.
- Each diff hunk maps to a matrix row.

**Fails the gate when** a changed file is outside the approved list, untouched lines were
reformatted, or pre-existing dead code was deleted without instruction.

---

## 4. Goal-driven execution

**Operating rule.** Define how success is proven before writing code, and report that proof at the
end. Multi-surface work is only done when every surface is covered or every exclusion is recorded.

**Enforced at** (design → Gate 2; review → Gate 4; finalise → final gate):
- A named **proving test** is required at Gate 2: the assertion that fails pre-change, passes
  post-change, runnable via `config.test_command`.
- The test result is reported at review, including "would it fail without the change?".
- The `N · k/N` denominator rule for every universal ("all/every/no") requirement: `k` surfaces
  covered out of total `N`.

**Fails the gate when** Gate 2 has no proving test, finalise records the test "not run" with no
command, or `k < N` with no recorded decision.
