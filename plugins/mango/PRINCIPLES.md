# PRINCIPLES.md — the binding contract

**A principle stated as prose does not bind; an emitted, counted artifact that blocks a gate
does.** Every mango skill references this file. A phase may not pass its gate until the artifacts
named below exist, are filled, and pass their own count/match checks. Silence is never approval.

The four principles follow. Each lists its **Operating rule**, where it is **Enforced at**, and
exactly when it **Fails the gate**.

> **Unattended runs do not weaken this, and `autorun` is not an exception to it.** `/mango:autorun`
> closes each gate on the **same** counted artifact the attended lane closes it on — it removes the
> human *keystroke*, never the gate, never the artifact, and never the review seat. Three properties
> keep "silence is never approval" true there: a counted line that does not parse against its shipped
> grammar **does not close its gate** (and is reported, never re-typed into the correct form); `j > 0`
> **stops** the run rather than guessing; and the only outward actions permitted are the two an
> explicit **handover authorisation** named up front — push the branch, open the PR. There is **no
> auto-merge**: the run ends when the PR exists, and the merge stays a human decision. Silence still
> approves nothing; the human's approval simply moves to the handover and the merge.

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
- **Falsifiable-or-excluded acceptance values.** Every acceptance value is either **falsifiable** (a
  measurable/greppable definition — not a vague adjective) **or** a recorded **manual-check
  exclusion** (unmeasurable → human-verified, logged up front as a coverage-gap exclusion). One that
  is **neither** is flagged at Gate 1 and **may not carry a matrix `✅`** — a bare self-reported `✅`
  cannot stand in for an unmeasurable or unbuilt thing.
- The `SECTIONS:` line (canonical form in `skills/analysis/SKILL.md`): sections **found** must equal
  sections **decomposed**. Every ticket section maps to ≥1 matrix row.
- **`RULE SECTIONS` coverage — by change type AND by recalled handle (union).** analysis derives the
  applicable rulebook sections **from the change type** (migration/schema → the DB-conventions section
  is mandatory; new UI surface → the design-token/a11y section is mandatory; …) **and, additively, from
  the `handle:` a promoted rule carries** when this run's `RECALL:` line surfaced that handle — without
  that second source a rule promoted from a lesson can never become applicable, and the lesson carries
  the constraint forever. `0` recalled handles adds `0` sections. Each applicable section is answered by
  **naming what in this change the rule constrains** — or marked N/A-with-reason; a bare `✅` with
  nothing named is not an answer. An applicable section left neither answered nor N/A is a finding
  (silently omitting the section that mattered is the miss this removes). A `PROVISIONAL` (unratified)
  section is surfaced and answered but **never gate-blocks as if it were codified**.
  Detect-and-surface only — mango never authors the rule.
- A `Rejected alternatives` line at design records what was considered and dropped.

**Fails the gate when** a gate is reached with `j > 0` unresolved, an AC mismatch was silently
changed instead of raised, sections found ≠ sections decomposed, an applicable rulebook section is
neither checked nor N/A-with-reason, or a vague acceptance value carries a `✅` without being pinned to
a measurable or recorded as a manual-check exclusion.

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
- **Blast-radius traces to real producers/consumers, not a name grep.** The design's change-list is
  the smallest **COMPLETE** set: a shared **type/symbol** change enumerates its factory/fixture
  patterns across **all test roots** (not just `src`) and runs `typecheck`; a **value threaded** to a
  downstream consumer enumerates **every builder/producer call site**, not just the owning surface. A
  shallow-grep estimate that misses a known producer/consumer is a Gate-2 finding — so `diff ⊆ approved
  change-list` holds at execute without deviation-recording backfilling it.

**Fails the gate when** a change-list item has no matrix row behind it, an introduced abstraction serves
only one call site, or the blast-radius estimate under-scopes a shared type's factories/test-roots or a
threaded value's producer call sites (a name grep standing in for tracing the real producers/consumers).

---

## 3. Surgical changes

**Operating rule.** Touch only what the approved change list requires. Match surrounding style.
Never reformat lines you are not changing. Run the project's formatter only on the files this change
authored or edited — never over a shared or pre-existing file wholesale; whole-file conformance is a
separate concern (CI or a dedicated chore ticket), never folded into this ticket's diff. Never delete
pre-existing dead code without instruction. **Scope discipline has two axes — the file set AND
conformance to the approved design behaviour; a clean file diff does not certify behavioural
conformance.**

**Enforced at** (execute → Phase 3; review → Gate 4):
- The **verification sweep**: proves zero stray references and that the diff ⊆ approved list.
- The diff ⊆ approved-list check and the "no reformatting untouched lines" review check.
- Each diff hunk maps to a matrix row.
- The **design-conformance self-check** (behaviour axis): execute walks each Gate-2 Approach bullet
  and classifies it `implemented-as-approved | deviated`; any `deviated` bullet is recorded as a
  deviation (traced to the approved bullet) and surfaced to review — **even when the file diff is a
  clean subset of the approved list**. review re-confirms this axis and treats a missed behavioural
  deviation, or a feature self-marked `✅` that was not implemented, as **not clean**.

**Fails the gate when** a changed file is outside the approved list, untouched lines were
reformatted, pre-existing dead code was deleted without instruction, or the implementation diverges
from an approved Gate-2 Approach bullet without that deviation being recorded — a green file diff
sitting over a wrong behaviour.

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
- **Baseline-aware Definition of Done (project-supplied, detect-not-assume).** `analysis` captures a
  `BASELINE: green | red | flaky` by running the verification command once on the untouched checkout
  (a clean checkout is **not** assumed green — a pre-existing or flaky failure is real). When
  `baseline ≠ green`, the DoD is **prove the delta is green**: the change introduces no new failure
  and fixes any it claims to; a pre-existing failure outside the change is a **recorded baseline
  exclusion**, neither a blocker nor a silent pass. `execute` proves against this baseline;
  `review`/`finalise` compare against it, never against a blanket "all green". mango **detects and
  records** the baseline; it never decides which pre-existing failures are acceptable — that is a
  human/rulebook call, logged.
- **Verify-only re-review after a conditional LGTM.** A round-1 `CHANGES REQUESTED` may be qualified
  as a **conditional LGTM** ("LGTM once findings 1–N land as described"); the re-review is then a
  **verify-only pass** (confirm the N named fixes + a regression scan) rather than a full requirement
  re-derivation. The ticket-blind `challenger`'s full re-derivation runs **once** and is not repeated
  on a verify-only round unless a fix changed scope — its independence is preserved, its cost is not
  paid twice for pure re-confirmation.
- The test result is reported at review, including "would it fail without the change?".
- The **stale-review guard** at finalise is **mechanical**: it diffs the live tree against the
  `Reviewed at <sha>` marker, exempts the working-doc / bookkeeping paths, and is stale **iff a source
  file changed beyond the reviewed set** — never a commit-*count* test, so the marker/bookkeeping bump
  alone cannot dead-lock it. A bare "go" never clears it; only a fresh review covering the current tree
  does.
- The `N · k/N` denominator rule for every universal ("all/every/no") requirement: `k` surfaces
  covered out of total `N`.

**Fails the gate when** Gate 2 has no proving test, a proving artifact sits below the layer where
its requirement can fail (a layer-match `❌`), finalise records the test "not run" with no command,
or `k < N` with no recorded decision.

> **Lessons are repo artifacts, not personal memory.** A durable lesson — a constraint discovered,
> a wrong assumption, or a process gap — belongs in `config.lessons_path` (a committed repo file),
> never only in an assistant's personal memory. `finalise` asks for one on **every** run,
> independent of whether any matrix row was deferred.

> **The shipped CHANGELOG is the retro's neutral source.** An independent field retro reads
> `<mango>/CHANGELOG.md` (shipped *inside* the plugin, alongside `plugin.json`) as the
> neutral record of "what changed this version" — never a prior retro's write-up, which would compound
> one reviewer's framing. `scripts/validate.py` requires that CHANGELOG to ship and to carry an entry
> matching the manifest version.

---

## Resolving a mango-shipped path — `<mango>`

> **`<mango>` is this plugin's root. Resolve it in this order; never as a hardcoded user path.**

1. `${CLAUDE_PLUGIN_ROOT}` when the host sets it.
2. Else the plugin root the **currently loaded skill file** came from — the directory holding the
   `skills/` tree the running `SKILL.md` sits in.
3. Else a **read-only** search for a directory carrying both `PRINCIPLES.md` and
   `.claude-plugin/plugin.json` under the host's plugin/extension roots.
   **More than one candidate is the normal case, not the exception** — a host keeps every installed
   version side by side, and a field host returned **eight**. So the search **counts** its candidates
   and selects the one whose `.claude-plugin/plugin.json` carries the **highest `version`**, compared
   as **semver** (numeric field by numeric field: `1.10.0` > `1.8.0`) — **never** the first result the
   search happened to return, and **never** a lexicographic string sort (which puts `1.8.0` above
   `1.10.0`). Report both: `PLUGIN ROOT: <n> candidate(s) found — using <path> (version <x.y.z>)`.
   Selecting by search order silently loads an older contract while `doctor` prints the newer number,
   so the count is part of the answer, not decoration.
4. Else `<mango>` is **UNREACHABLE**: say so in one line, use the **inline fallback** the point of use
   names, and report the degradation. Never guess a path, never invent a home directory, and never
   continue as if the file had been read.

Every `<mango>/…` reference — in a skill, an agent brief, or a template — resolves through this order.
`${CLAUDE_PLUGIN_ROOT}` is step 1, not the contract: a host that never sets it still resolves.

---

## On-demand companions — every one is READ at its point of use

This file is the **always-loaded core** (the four principles, the resolution order above, the
model-delegation map). Each companion below is read **on demand** by the phase that applies it, under
an explicit READ instruction in that skill — a companion nobody is told to read is content that never
reaches the agent. Relocation changed **where** the text lives, never what it says.

| companion (under `<mango>/principles/`) | READ by | when |
|---|---|---|
| `git-isolation.md` | `review` | always, before any review subagent |
| `learning-loop.md` | `finalise` | always, at the learning-loop step |
| `refine.md` | `refine` | always, at Phase 0 |
| `maturity.md` | `breakdown` | always, on the epic path |
| `descriptive-normative.md` | `codify`, `sitemap`, `db-map` | always, when that skill runs |
| `token-cost.md` | `budget` | always, when that skill runs |
| `frontend-track.md` | `analysis`, `design`, `execute`, `review` | when `config.track` includes frontend |
| `authoring.md` | mango's **maintainer** (`CONTRIBUTING.md`) | when editing a mango skill — never on a ticket run |

A companion is **contract text, never a substitute for a directive**: the skill that must act still
carries its own instruction.

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
