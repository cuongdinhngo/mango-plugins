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
- **Gate 2 is blocked when an integration/runtime AC is backed only by a logic-layer proof; the
  layer-match is enforced, not advisory.** Gate 2 carries a per-AC **verification plan** (risk layer
  vs proof artifact, with a binding layer-match check). A layer-match `❌` blocks Gate 2 and passes
  only when the proof is upgraded to the matching layer **or** the row is recorded as a
  human-approved coverage-gap exclusion — never a silent pass.
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

## Descriptive vs normative — observe, facilitate, never author

> **mango generates the descriptive and facilitates the normative, but never authors the normative.**

A **descriptive** artifact is a *fact* about what the code or schema **is** — regenerable and
falsifiable (a code sitemap, a database schema map). mango may generate these freely; they are
opt-in, stack-specific adapters (`sitemap`, `db-map`), never core to the lifecycle and never on by
default.

A **normative** artifact is a *rule* — what the code **should** do (the engineering rule book,
database conventions). mango may **facilitate** defining these by **counting the observed patterns
and asking the human to choose** (the `codify` skill), but it must:
- **NEVER author a rule itself**, and never pick, recommend, or default to the majority. Presenting
  "pattern A: 12 files, B: 5" is **data**; concluding "so A is the rule" is **authoring — forbidden**.
- **Never treat "what the code does" as "what the rule should be."** Consistency observed is not
  consent given.
- Tag every recorded standard **`PROVISIONAL (awaiting ratification)`** and keep it provisional until
  a human **explicitly ratifies** it. A provisional draft is a draft for the team — not one person's
  preference frozen as law.

Enforced at `codify` (the counted report + the per-dimension human choice + the ratification gate)
and guarded by `scripts/validate.py` (the boundary tokens). The descriptive adapters change no source
and no schema.

---

## Frontend track — own the durable, compose the volatile

> **mango embeds only UI knowledge that is durable + falsifiable; it composes, never owns, the
> aesthetic-generation layer — and never stops because a taste skill is missing.**

Active only when `config.track` includes frontend (default `backend` — unchanged behaviour). `track`
is **orthogonal to TIER**: TIER is process weight, track is which gate set applies.

- **Falsifiable-only rubric.** Every frontend rubric item is **measurable or greppable** and scored
  **against the project's `DESIGN.md`** (`config.design_doc_path`). Any "is it tasteful?" judgment is
  **out of the rubric** — taste exists only as `DESIGN.md` conformance. A blanket rule (e.g. "ban
  colour X") **yields to domain meaning** recorded in `DESIGN.md` — a domain term may literally denote
  that colour, so the reviewer checks the contract, not a blanket rule.
- **Compose, never own, the aesthetic.** mango embeds only durable, measurable knowledge (a11y
  thresholds, token-first, `DESIGN.md` conformance). The aesthetic-*generation* layer is **composed**:
  call an external taste skill if installed, else follow `DESIGN.md`. **Never stop because a taste
  skill is missing** — mango blocks on a missing **number**, never on a missing aesthetic. Breakpoint
  values, the narrow-width navigation pattern, and which regions collapse vs reflow are **choices** →
  they live in `DESIGN.md`, never gated by mango.
- **Risk-layer floor (so the layer-match gate cannot be diluted).** Frontend ACs ride the **same**
  layer-match hard gate as Principle 4 — not a fork. `document`, `computed-style`,
  `integration/runtime`, and `behavioral` are **all above the logic/unit layer**: a unit-only proof
  (a mocked DOM) clears **none** of the M1–M10 gates; `computed-style` requires a **real resolved
  DOM**. A proof below an AC's risk layer is a layer-match `❌` and **blocks Gate 2** unless upgraded
  or recorded as a human-approved coverage-gap exclusion.

Enforced at `analysis` (the `TRACK` artifact), `design` (the `DESIGN.md` contract + layer-matched
verification plan), `execute` (token-first + Pointer Events), and `review` (the rubric scored against
`DESIGN.md`); guarded by `scripts/validate.py` (the track tokens). The M10 pointer-parity gate
**degrades gracefully** — an always-on greppable smell can block, while the behavioral dispatch-assert
runs only when the environment can and is otherwise a recorded exclusion, so it never wedges review.

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
| Review verdict + challenger requirement reconstruction | judgment (highest) | Sonnet — the `reviewer-max` agent (Opus) for high-stakes diffs under `cost_tier: max` — **never Haiku** |
| Implement the approved change list; draft PR body | execute | Sonnet |
| Explore: locate handler, callers, blast radius | retrieval + light judgment | Sonnet |
| Bulk read-and-extract / summarise across many files | heavy tokens, low judgment | Haiku |
| grep stray refs / run tests / lint | pure shell | no model — call the Bash tool directly |

`config.cost_tier` (`economy | standard | max`, default `standard`) shifts the dials within this
map — never against it. `economy` pushes more retrieval to Haiku and avoids Opus on review;
`standard` is the map above; `max` dispatches the **`reviewer-max`** agent (Opus) for high-stakes
diffs (security-tagged, or touching auth / data access / schema migration). Because a skill cannot
re-pin a subagent's model at runtime, the Opus upgrade is a **choice of agent** (`reviewer-max` vs
`reviewer`), not a runtime setting — `review` selects it explicitly. `reviewer` and `reviewer-max`
are never Haiku, and `challenger` is never pinned to Haiku. The **lite** tier runs on a single
model — no delegation overhead. Never spawn a model for a one-line shell command (grep/test/lint) —
run the Bash tool.
