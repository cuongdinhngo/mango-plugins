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

> **Challenger independence is procedural, backed by a path separation — not cryptographic.** The
> working doc lives at `<config.work_dir>/<KEY>.work.md`, a **separate path** from the ticket spec,
> so the orchestrator can build the challenger's input from the re-fetched raw ticket + diff and
> simply leave the `.work.md` out. The "ticket-blind" property still holds only because the
> orchestrator upholds that withhold-and-re-fetch discipline — nothing cryptographically prevents a
> leak. Treat it as a discipline backed by structure, and state the limit honestly rather than
> overclaiming guaranteed independence.

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
- **The proving test must sit at the layer where the requirement can fail; a logic-layer proof for
  an integration/runtime requirement is false confidence, not coverage.** Gate 2 carries a per-AC
  **verification plan** (risk layer vs proof artifact, with a layer-match check) and may not pass
  with any layer mismatch.
- The test result is reported at review, including "would it fail without the change?".
- The `N · k/N` denominator rule for every universal ("all/every/no") requirement: `k` surfaces
  covered out of total `N`.

**Fails the gate when** Gate 2 has no proving test, a proving artifact sits below the layer where
its requirement can fail (a layer-match `❌`), finalise records the test "not run" with no command,
or `k < N` with no recorded decision.

> **Lessons are repo artifacts, not personal memory.** A durable lesson — a constraint discovered,
> a wrong assumption, or a process gap — belongs in `config.lessons_path` (a committed repo file),
> never only in an assistant's personal memory. `finalise` asks for one on **every** run,
> independent of whether any matrix row was deferred.

---

## Model delegation (strong model decides, weak model gathers)

> **"Opus decides, Sonnet executes, Haiku gathers — and every decision or verdict must be produced
> or ratified by the strong model; a weaker model may only gather, never conclude."**

Route work by the **nature of the task (judgment vs retrieval)** — NOT by phase position
(early/late) or role label (main/sub). The trap to avoid: review and the challenger *look* like
"heavy checking", but finding unmet requirements is the **highest-judgment** step in the flow. Never
demote it to a weak model — a weak model misses items yet asserts confidently, which is exactly the
silent under-delivery mango exists to prevent. A high-stakes diff warrants a *stronger* reviewer,
not a weaker one.

| Step | Nature | Model |
|------|--------|-------|
| Orchestrator + gates (decide) | judgment | the strong model the user drives (Opus) |
| Analysis: root cause/gap, requirements decomposition, AC validation, clarification, scope | judgment | Opus |
| Design: smallest change list, proving test | judgment | Opus |
| Review verdict + challenger requirement reconstruction | judgment (highest) | Sonnet — Opus for high-stakes diffs — **never Haiku** |
| Implement the approved change list; draft PR body | execute | Sonnet |
| Explore: locate handler, callers, blast radius | retrieval + light judgment | Sonnet |
| Bulk read-and-extract / summarise across many files | heavy tokens, low judgment | Haiku |
| grep stray refs / run tests / lint | pure shell | no model — call the Bash tool directly |

`config.cost_tier` (`economy | standard | max`, default `standard`) shifts the dials within this
map — never against it. `economy` pushes more retrieval to Haiku and avoids Opus on review;
`standard` is the map above; `max` allows Opus on review for high-stakes diffs. `reviewer` and
`challenger` are never pinned to Haiku. The **lite** tier runs on a single model — no delegation
overhead. Never spawn a model for a one-line shell command (grep/test/lint) — run the Bash tool.
