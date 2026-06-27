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
- **Verification sweep:** zero stray references ✅/❌ · diff ⊆ approved list ✅/❌ · each hunk maps to a row ✅/❌
- **Design-invalidation / re-gate** (fill only if a test or the proving test shows the approved
  Gate-2 approach cannot work as designed): what failed + evidence (`path:line` / test signature) ·
  STOP recorded ✅ · options surfaced to user · **Gate 2 re-opened** with a revised approach
  (re-passes Assumptions + verification-plan). Never "continue with a known-broken approach."

## Phase 4 — Review ✋ (stop only if not clean)

- reviewer verdict (BLOCK / CHANGES REQUESTED / LGTM):
- challenger (ticket-blind) result:
- security agent (if any):
- Scope reconciliation (files outside list / reformatting):
- Regression on Phase-1 callers:
- Proving test result + "would it fail without the change?":
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
  - [ ] open PR via pr_host
  - [ ] tracker comment (via tracker.cli)
  - [ ] tracker transition (via tracker.cli)
- Follow-up tickets drafted for deferred (⚠) rows:
- **Durable lesson** (asked on EVERY run, independent of deferred rows — a constraint discovered, a
  wrong assumption, or a process gap): none / `<lesson>` written to `config.lessons_path` (a repo
  artifact, never only personal memory):
- Revert path:

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
