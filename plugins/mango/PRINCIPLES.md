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
- **Falsifiable-or-excluded acceptance values.** Every acceptance value is either **falsifiable** (a
  measurable/greppable definition — not a vague adjective) **or** a recorded **manual-check
  exclusion** (unmeasurable → human-verified, logged up front as a coverage-gap exclusion). One that
  is **neither** is flagged at Gate 1 and **may not carry a matrix `✅`** — a bare self-reported `✅`
  cannot stand in for an unmeasurable or unbuilt thing.
- `SECTIONS: <n> found = <n> decomposed`. Every ticket section maps to ≥1 matrix row.
- A `Rejected alternatives` line at design records what was considered and dropped.

**Fails the gate when** a gate is reached with `j > 0` unresolved, an AC mismatch was silently
changed instead of raised, sections found ≠ sections decomposed, or a vague acceptance value carries
a `✅` without being pinned to a measurable or recorded as a manual-check exclusion.

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
- **Surface coverage — the denominator comes from the CODE, not the ticket.** A universal / app-wide
  frontend requirement (no horizontal scroll, reflow, focus-visible, contrast — anything page-wide)
  has its denominator **N = |reachable surfaces|** enumerated from the code surface (the opt-in
  `sitemap`, else a read-only "enumerate reachable views" sub-step). The ticket's examples are a
  **hint, never the denominator** — counting only the surfaces the ticket named is the exact failure
  this removes. `analysis` emits `SURFACES: N` (counted, challenger-checkable); the gate passes iff
  `N == M + X` (`M` = surfaces with a valid proof at any tier, `X` = recorded exclusions), with a loud
  `surfaces proven: k/N` banner whenever `M + X < N`.
- **Elastic proof tier — e2e is optional, a proof is not.** Per affected surface, `execute` produces
  the **highest available tier**: `PASS(automated)` (tier-1, satisfying the C1–C8 automated-proof
  contract by composing the **project's** runner — mango bundles none) → `PASS(render@<bp>)` (tier-2,
  a recorded render of the real surface at the breakpoint asserting the visible measurable — a
  **first-class proof, not an exclusion**) → `EXCLUDED` (human-approved, only when neither is
  reachable). Dropping a tier because there is no runner is fine; dropping to *nothing* is not. mango
  **never stops for a missing runner** — it scaffolds tier-1 (per `templates/ui-proof-scaffold.md`),
  else records a tier-2 render proof, else an exclusion.

Enforced at `analysis` (the `TRACK` + `SURFACES` artifacts), `design` (the `DESIGN.md` contract +
layer-matched, surface-aware verification plan + under-coverage banner), `execute` (token-first +
Pointer Events + the elastic-tier proof manifest), and `review` (the rubric scored against `DESIGN.md`
+ the `N == M + X` surface check, re-running ≥1 proof); guarded by `scripts/validate.py` (the track +
surface/manifest tokens). The M10 pointer-parity gate **degrades gracefully** — an always-on greppable
smell can block, while the behavioral dispatch-assert runs only when the environment can and is
otherwise a recorded exclusion, so it never wedges review. **Own** the coverage rule, the tier ladder,
the manifest schema, and the runner-agnostic scaffold spec; **compose** the runner itself.

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

## Token cost — measure before you optimize (descriptive ledger + human-gated optimizers)

> **mango measures its own token cost as a counted, descriptive artifact, and adopts a token
> optimizer only through a human gate with the safety trade-offs made explicit — it never installs
> one, never depends on one, and never lets one weaken a check, a gate, a critic, or the evidence a
> critic emits.**

- **The Cost ledger is descriptive.** The run records token usage **per subagent dispatch** (reviewer,
  challenger, extractor, Explore fan-out, each review round) into the working doc as a **facts-only**
  counted artifact — **one row emitted per dispatch return as a mechanical by-product of dispatching**
  (N dispatches → N rows), not bookkeeping the model is asked to remember; `finalise` surfaces a
  one-line summary (total + top cost driver). It **never** auto-cuts anything — it makes cost **visible**
  so a *human* can decide. Cost was always an **estimate**, never measured per-phase; `context ≠
  correctness` applied to optimization means **don't optimize what you haven't measured** — the ledger
  is that measurement, and the data a later middle-tier sizing decision needs. The ledger is
  **dispatch-scoped**: it measures subagent dispatch only — main-loop output noise is **not measured by
  mango**, so it implies no dispatch-vs-noise split; the optimizer reports its **own** savings (`rtk
  gain`) for that domain. **Ledger completeness is gate-checked at finalise** (the ledger's teeth):
  the ledger is complete only when **every dispatch row is present AND its token cell carries a value** —
  a real count or the explicit `unmeasured (blocking retrieval)` marker; a missing row **or** a blank
  token cell is incomplete and blocks like an unfilled matrix column. It checks the **presence** of a
  value or an honest marker — it never inspects, ranks, judges, invents, or auto-cuts a value — so the
  ledger stays descriptive.
- **The safety axis (governs every optimizer choice).** An optimizer is **safe** only if it removes
  **representation redundancy** — *how* output is phrased — and **never** a check, a gate, a critic,
  or the **evidence detail** a critic relies on (`path:line`, measured values, per-clause verdicts,
  diffs). **RTK** (compresses Bash-command output before it enters context) is safe and sits **below**
  mango. **Headroom** input compression is safe, but its `OUTPUT_SHAPER` / effort-routing changes what
  the model writes and how hard it thinks → it **must stay OFF** for mango. **Caveman** (terse agent
  output) optimizes exactly what mango refuses for critics.
- **RTK default-expect + degrade cleanly.** The default `token_optimizer.rtk: "expect"` means mango
  **tolerates** RTK rewriting Bash output into a compact form; it does **not** install RTK and does
  **not** require it. If RTK is absent, everything runs **identically** — only the saving is lost.
  mango must never fail, block, or change a decision on RTK presence/absence, and no mango logic may
  parse an RTK-specific format in a way that breaks without RTK.
- **Caveman critic guardrail (HARD — invariant).** Caveman-style output compression **must never** be
  applied to critic output — the `reviewer`, the `challenger`, and any gate-blocking artifact — which
  **must retain full evidence detail** (`path:line`, measured values, per-clause verdicts). Terse
  critic output loses the evidence that **is** the review's value; **brevity is never applied where a
  false-green could hide** — the retro-#5 class, where a self-reported ✅ stood in for an unproven
  thing. Caveman, if enabled, is **scoped to non-critic output only** (`caveman.scope:
  "non-critic-only"`) and mango enforces it.

Adoption of any optimizer is a **recorded, PROVISIONAL decision** (via `/mango:budget`, ratified like
`codify`), never a silent toggle. Enforced at `budget` (detect + inform + the recorded human choice),
the `reviewer`/`reviewer-max`/`challenger` briefs (the critic guardrail), and `scripts/validate.py`
(the `budget` contract, the `token_optimizer` schema, and the critic-guardrail token).
