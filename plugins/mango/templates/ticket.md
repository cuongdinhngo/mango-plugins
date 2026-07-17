<!-- WORKING-DOC TEMPLATE. Copied by `analysis` to `<config.work_dir>/<KEY>.work.md` — the mutable
state doc that carries all five phases. It is SEPARATE from the ticket spec: never append this to,
or merge it into, the raw ticket / ticket spec file. The challenger is given only the re-fetched raw
ticket + the diff, never this `.work.md`. -->

# <KEY> — <ticket title> (working doc)

- **Ticket:** <KEY> · <tracker link>
- **Type:** bug | enhancement
- **Repo(s) / Porting:** <which config.repos are touched; porting order if shared>
- **SCOPE:** S | M | L
- **STRUCTURE:** native | synthesized  <!-- synthesized → freeform ticket; confirm reading at Gate 0 -->
- **TRACK:** backend | frontend | fullstack  <!-- counted artifact from analysis; orthogonal to TIER; selects which gate set (frontend adds the a11y/token + M1–M10 rubric) -->
- **TIER:** lite | full  <!-- lite routes through /mango:quick; full = five-phase flow -->
- **BASELINE:** green | red | flaky  <!-- analysis runs config.test_command once on the untouched checkout; if red/flaky, list the specific pre-existing failing items below. When baseline≠green the DoD is "prove the delta is green": no new failure, fix any claimed; a pre-existing failure outside the change is a recorded baseline exclusion, not a blocker and not a silent pass. review/finalise compare against THIS, never "all green". -->
  <!-- baseline exclusions (pre-existing failures outside this change): <list, or none> -->

---

## Phase 0 — Refine (the FIRST phase; skip when the ticket is already clear)

`refine` scans the project, TRIES to expose the unresolved product-decisions, and its count IS the
gate. Every decision here is a **counted artifact**, never prose. refine **exposes for the human to
decide and never authors intent**.

`REFINE: <U> unresolved surfaced | <a> want-decision asked | <b> how-decision resolved+cited | <s> ASSUMED | skip: yes/no`

<!-- skip: yes → U=0, record `refine skipped: 0 unresolved product-decisions` and hand to analysis; this line is the whole Phase-0 output. -->
<!-- INPUT KIND: ticket | epic. On epic → epic path (analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles), v1-learning. -->

**Settled wants (want-decision — from the user; become acceptance-criteria constraints analysis must honour).**
Tie-breaker: a decision about the acceptance BAR itself (what counts as done / a threshold / a sourcing
standard) is a want-decision by default, even when it looks derivable — the user owns the bar.

| # | The want (in want-language) | Chosen direction (NOT a tool) | Becomes AC constraint |
|---|-----------------------------|-------------------------------|-----------------------|
| 1 |                             |                               |                       |

**Resolved direction + citation (how-decision — refine-resolved + CITED; a starting premise, analysis still
picks the tool).** Every row MUST carry a citation — an **uncited how-decision resolution is a finding**
(it usually means a mis-classified want-decision, e.g. an acceptance-bar decision the user owns):

| # | HOW-decision | Resolution | Citation (`file:line` / convention / rulebook § / ticket line) |
|---|--------------|------------|----------------------------------------------------------------|
| 1 |              |            |                                                                |

**ASSUMED (awaiting ratification) — MANDATORY, not optional.** Any want-decision the user hands back
("your call") or that refine resolves as an assumption **MUST** be recorded here with the `ASSUMED`
tag — recording it as settled prose is a finding. It requires an **explicit human confirm at the next
gate** (Gate 1 / design) before it counts as ratified — not a gate that "happened to re-mention it".
Tripwire: never silent-settle over a prior human decision.

| # | Assumed choice | Why ASSUMED (handed back / recommendation) | Explicit confirm at gate | Reverses a prior decision? |
|---|----------------|--------------------------------------------|--------------------------|----------------------------|
| 1 |                |                                            |                          | yes / no                   |

**Constraints surfaced from the scan** (rule book / design tokens / policy the user couldn't know to ask):

-

**Exposure-checker** (ticket-blind `challenger`, **1 dispatch** — NOT a debate): any still-un-exposed
decision it found (re-classified want-decision/how-decision above): none / <list>

<!-- Split mixed input: an open brainstorm bundled with a targeted task is separated — refine refines only the targeted part. Record what was set aside: -->

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

Every acceptance value must be **falsifiable** (a measurable/greppable definition — not a vague
adjective) **or** a recorded **manual-check exclusion** (unmeasurable → human-verified; log it in
*Coverage-gap exclusions* below). One that is **neither** is flagged here and **may not carry a
matrix `✅`**; pin a vague word to a measurable form as a Gate-1 question.

| AC ID | Ticket states | Independently computed | Match? | Falsifiable? (measurable/greppable · manual-check exclusion · **neither → flag**) | If mismatch / not falsifiable → Gate-1 question |
|-------|---------------|------------------------|--------|-----------------------------------------------------------------------------------|-------------------------------------------------|
|       |               |                        | Y/N    |                                                                                   |                                                 |

## Inventory (universal "all/every/no" requirements)

- **Denominator / total N:** <N>
- Numbered list of every affected item:
  1.
  2.

For a counted **"do X for each of N"** requirement, this numbered list **is** the per-item checklist:
one row per item, not a single aggregate row. Review fills each row item-by-item — it is not clean
until **every** item is confirmed (or each unconfirmed item is a recorded, human-approved
coverage-gap exclusion). An aggregate "k/N" alone does not close a "for each" requirement.

| # | Item | Ph3/4 proven by (`path:line` / test) | Status ✅/⚠/❌ |
|---|------|--------------------------------------|----------------|
| 1 |      |                                      |                |
| 2 |      |                                      |                |

### Surface inventory (universal / app-wide FRONTEND requirements only)

For any frontend requirement phrased all/every/no **or inherently page-wide** (no horizontal scroll,
reflow, focus-visible, contrast …), the denominator **N is the count of reachable surfaces enumerated
from the CODE — never from the ticket prose**. Consult the opt-in `sitemap` (`config.docs_dir/sitemap.md`);
if absent, enumerate reachable views read-only. The ticket's examples are a *hint*, never the denominator.

`SURFACES: <N> — <route / full-window overlay / modal / major mounted state>, …`

| # | Surface (route / overlay / modal / state) | Can the change affect it? |
|---|-------------------------------------------|---------------------------|
| 1 |                                           | yes / no                  |
| 2 |                                           | yes / no                  |

## Clarifications

`CLARIFICATION: <M> raised | <k> self-resolved (cited) | <j> for human decision`

- Self-resolved (with citation: rulebook §, `path:line`, or ticket line):
- For human decision (**if any, STOP at Gate 0**):

---

## Phase 1 — Analysis ✋ Gate 1

- Root cause (bug, classified vs cause_taxonomy) **or** per-goal gap analysis (enhancement), with `path:line`:
- Handler / entry point + blast radius (callers, dependents):
- **Rule-compliance section coverage** — applicable rulebook sections **derived from the change type**
  (migration/schema → DB-conventions mandatory; new UI surface → design-token/a11y mandatory; …), each
  checked or N/A-with-reason; an applicable section left unchecked is a finding:

  `RULE SECTIONS: <applicable §s by change-type> — each checked ✅ / N/A (reason)`
- Self-audit:
- **Gate 1 status:** waiting on user / cleared

## Phase 2 — Design ✋ Gate 2

- Approach:
- Rejected alternatives:

**Assumptions** (Gate 2 may not pass with an unresolved `novel-untested` 3p/runtime assumption —
resolve via a recorded spike OR an integration/e2e-shaped proving test):

| Assumption | verified / novel-untested | If novel-untested 3p/runtime → spike result OR integration-shaped proving test |
|------------|---------------------------|--------------------------------------------------------------------------------|
|            |                           |                                                                                |

- Smallest change-list (every item traces to a matrix row): see matrix `Ph2 covered by`.
- Rule compliance (vs rulebook_path / standards_path):
- **Proving test** (fails pre-change, passes post-change; invocation via test_command):

**Verification plan** (one row per AC / at-risk requirement; the proof must sit at the layer where
the requirement can fail — **Gate 2 may not pass with any ❌**):

| AC | risk layer (logic / integration / runtime-3p / e2e) | proof artifact (unit / integration / e2e / manual-recorded) | layer-match? ✅/❌ |
|----|------------------------------------------------------|-------------------------------------------------------------|-------------------|
|    |                                                      |                                                             |                   |

**Coverage-gap exclusions** (any verification-plan `❌` that is deliberately deferred instead of
upgraded — each needs human approval; a recorded exclusion lets the review gate pass and tells the
challenger's "not met" apart from an unmet requirement):

| Item | Risk tier | Why deferred | Follow-up |
|------|-----------|--------------|-----------|
|      |           |              |           |

**Proof manifest — surface-aware (frontend integration/runtime/behavioral ACs).** `design` lays out
**one row per (AC × affected surface)** from the Surface inventory; `execute` fills the tier + proof;
`review` scores it. Proof tier is **elastic but never optional** — `automated` (tier-1, satisfies the
C1–C8 automated-proof contract) → `render@<bp>` (tier-2, a recorded render/screenshot of the real
surface at the breakpoint asserting the visible measurable — a **first-class proof, not an
exclusion**) → `excluded` (human-approved, only when neither tier is reachable). e2e is the *top* tier
when a runner exists, **not** the only acceptable proof.

| AC | surface | risk-layer (integration/runtime/behavioral) | tier (automated / render@<bp> / excluded) | proof-cmd \| artifact | asserts (measurable) | status: PASS(automated\|render@<bp>) / EXCLUDED(approver, reason) |
|----|---------|---------------------------------------------|-------------------------------------------|------------------------|----------------------|-------------------------------------------------------------------|
|    |         |                                             |                                           |                        |                      |                                                                   |

**Surface coverage count.** For each universal/app-wide frontend requirement: `N` = |Surface
inventory|, `M` = surfaces with a valid PASS (any tier), `X` = recorded EXCLUDED. **Gate 2 passes iff
`N == M + X`.** When `M + X < N`, emit the loud banner (as unmissable as an unfilled matrix column):

`⚠ surfaces proven: <M+X>/<N> — <uncovered surfaces> have no proof; cover or record an exclusion.`

- Rollback + porting plan across repos:
- **DESIGN.md** (frontend track only): created/updated at `config.design_doc_path` — palette
  domain-first, shell/data-core split, Responsive & touch choices (breakpoints, nav pattern,
  collapse/reflow, thumb-zone, motion): n/a / done
- SCOPE confirmed:
- **Gate 2 status:** waiting on user / cleared

## Phase 3 — Execute

- Branch:
- Commits (logical units; no AI co-author trailer):
- Proving test added:
- **Verification sweep — BOTH axes.** *File axis:* zero stray references ✅/❌ · diff ⊆ approved list ✅/❌ · each hunk maps to a row ✅/❌. *Behaviour axis (design-conformance self-check):* walk each Gate-2 Approach bullet, classify `implemented-as-approved | deviated`; a clean file diff does not certify behavioural conformance.
- **Design-conformance deviations** (any Gate-2 Approach bullet implemented differently from what was approved — recorded even when every touched file is in the change-list; surfaced to review for adjudication):

  | Approved Gate-2 bullet | What was implemented instead | `path:line` | Surfaced to review |
  |------------------------|------------------------------|-------------|--------------------|
  |                        |                              |             |                    |

- **Design-invalidation / re-gate** (fill only if a test or the proving test shows the approved
  Gate-2 approach cannot work as designed): what failed + evidence (`path:line` / test signature) ·
  STOP recorded ✅ · options surfaced to user · **Gate 2 re-opened** with a revised approach
  (re-passes Assumptions + verification-plan). Never "continue with a known-broken approach."

## Phase 4 — Review ✋ (stop only if not clean)

- reviewer verdict (BLOCK / CHANGES REQUESTED [/ conditional LGTM] / LGTM):
- Re-review path (if round 1 was CHANGES REQUESTED): full / **verify-only** (round 1 was a conditional LGTM → **main-loop, no re-dispatch**: confirm findings 1–N landed + re-run only the affected proof + regression scan; challenger re-derivation NOT repeated; re-dispatch a reviewer/challenger ONLY if a fix changed scope):
- challenger (ticket-blind) result:
- security agent (if any):
- Scope reconciliation (files outside list / reformatting):
- Regression on Phase-1 callers:
- Proving test result + "would it fail without the change?" (judged vs the recorded `BASELINE`, not "all green": when baseline≠green the bar is delta-green — no new failure, claimed fixes landed; a pre-existing failure outside the change is a recorded baseline exclusion):
- Layer-match re-confirmation (no AC closed clean on a layer-mismatched proof; any `❌` is upgraded or a recorded exclusion):
- **Frontend rubric** (frontend track only — scored against `DESIGN.md`): Core (tokens / no hardcoded hex-px / semantic HTML / state-not-by-colour-alone / reduced-motion) + M1–M10 (viewport, no-h-scroll @breakpoints+320, reflow, touch-target, input-zoom, tap/hover parity, focus-visible, contrast, safe-area, pointer parity); M10 smell ran + dispatch-assert run-or-recorded-exclusion: n/a / pass / findings
- **Proof-manifest / surfaces proven** (frontend universal/app-wide reqs): challenger scores each row
  (tier-1 vs C1–C8, tier-2 vs the render-proof contract), re-runs/confirms ≥1 proof (lite: confirm
  command/artifact present), and checks `N == M + X` per requirement. `surfaces proven: <M+X>/<N>` —
  any `M + X < N` blocks (emit the banner): n/a / <M+X>/<N>
- `Ph3/4 proven by` filled (k/N): see matrix.
- **Clean?** reviewer no Critical AND challenger every item met AND no layer-match ❌ unresolved AND k=N (or exclusions approved) AND **surfaces proven N==M+X** AND proving test green → yes/no
- **Reviewed at** (stale-review guard — recorded on a clean verdict): `<commit SHA>` · reviewed files: `<list>`. `finalise` refuses to open a PR if `HEAD` / the diff moved beyond this set, routing back here for a re-review.

## Phase 5 — Finalise ✋ final gate

- PR draft: `/tmp/pr-<KEY>.md`
- Planned outward actions (each needs separate approval):
  - [ ] push branch
  - [ ] push bookkeeping commit (durable lesson / BACKLOG → shared ref; idempotent; fold into the
        branch-push when it rides the same branch)
  - [ ] open PR via pr_host
  - [ ] tracker comment (via tracker.cli)
  - [ ] tracker transition (via tracker.cli)
- Follow-up tickets drafted for deferred (⚠) rows:
- **Durable lesson** (asked on EVERY run, independent of deferred rows — a constraint discovered, a
  wrong assumption, or a process gap): none / `<lesson>` written to `config.lessons_path` (a repo
  artifact, never only personal memory) and landed on a **shared/pushed ref**, not only a local branch:
- Revert path:

---

## Cost ledger (descriptive — facts only, never auto-cuts)

A **counted artifact** recording token usage **per subagent dispatch** (reviewer, challenger,
extractor, Explore fan-out, each review round), transcribed from each return's usage block. **One row
is emitted per dispatch return — a run that dispatched N subagents ends with N rows** — as a mechanical
by-product of dispatching, not bookkeeping to remember (see `solve`). It reports **facts only**: phase,
subagent/dispatch, round, tokens. **Descriptive, never normative** — it makes the cost visible so a
*human* can decide where to trim; it never itself decides to cut a check, a gate, a critic, or evidence
detail. This is also the data the middle-tier sizing decision needs later — **measure before you size**
(`context ≠ correctness`: don't optimize what you haven't measured).

**Scope — dispatch-only (honest about what is and isn't measured).** The ledger measures **subagent
dispatch only**. Main-loop output noise (verbose lint/test/build dumps, file reads) is **not measured
by mango** — do **not** present a dispatch-vs-noise percentage as if both were counted; that split is
an instrumentation artifact, not a finding. For the output-noise side, consult the optimizer's own
analytics (`rtk gain` when RTK is live) — each layer measures its own domain. When a `token_optimizer`
is enabled (via `/mango:budget`), record what it is estimated/measured to save here too — measure the
optimizer, don't trust its claim.

The **Tokens** column carries the single figure the harness surfaces per dispatch return; it is **not**
split into in/out, so the column is labelled plainly `Tokens` (no unsupported `(out)` — don't claim a
precision the measurement doesn't have). Each row's Tokens cell carries **either** the real figure from
that return's `<usage>` block **or**, when the dispatch was retrieved by blocking and the environment
could not surface usage, the explicit marker **`unmeasured (blocking retrieval)`** — **never a silent
blank and never a fabricated number** (see `solve` for recovering a blocked dispatch's usage first). A
blank/absent token cell is an **incomplete** ledger and blocks finalise exactly as an unfilled matrix
cell blocks a gate (see `finalise`'s content-completeness gate).

| Phase | Subagent / dispatch | Round | Tokens | Optimizer applied · est./measured saving |
|-------|---------------------|-------|--------|------------------------------------------|
|       |                     |       |        |                                          |

`LEDGER TOTAL: <tokens> · top cost driver: <phase / subagent>` — surfaced by `finalise` at the final
gate as a one-line summary (total + top cost driver). It never triggers an automatic cut.

---

## Decision log

Record every gate decision here — including any **scope re-declaration** when the card *outgrew its
ticket* (realized scope crossed a tier, or the change type drifted from the branch/PR type): note the
old → new `SCOPE`/type and whether the excess was re-scoped or split into a follow-up.

| When | Decision | Why |
|------|----------|-----|
|      |          |     |

## Session status

- **Last updated:**
- **Current phase:**
- **Next action:** <concrete; never "continue">
- **Blocked on:**
