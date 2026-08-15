---
name: execute
description: Phase 3 of the mango ticket lifecycle. Use after design clears Gate 2. Implements ONLY the approved change list on a fresh branch, adds the proving test, runs a verification sweep proving the diff is a subset of the approved list, then flows straight to review. Autonomous (no gate).
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This phase enforces principle 3 (Surgical
changes) via the verification sweep and the diff ⊆ approved-list check.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`<mango>/config/harness.example.json`. This phase is autonomous — it does not stop at
a gate — but it implements ONLY what Gate 2 approved. Autonomy is **not** licence to thrash or to
barrel on with a broken approach: the two STOP conditions in **Escalations** below are mandatory.

**Model delegation** (see `<mango>/PRINCIPLES.md`): implementing the approved change
list and drafting the PR body are **execute** work — Sonnet. Bulk read-and-extract may go to the
Haiku `extractor` worker. Run the verification sweep's grep / tests / lint via the Bash tool
directly — never spawn a model for a one-line shell command.

## Steps

1. **Confirm Gate 2 cleared.** Read the working doc `<config.work_dir>/<KEY>.work.md`: approved
   change list, proving test, and `SCOPE` must be present. If not, return to design.
2. **Branch.** Create a branch per `config.branch_strategy` (default `fix|feat|chore/<KEY>-<slug>`)
   in the target repo's `config.repos[].root`. One branch for the approved work.
3. **Implement the approved change list — and only it.**
   - Make exactly the changes in the Gate-2 list; nothing more.
   - Match surrounding style.
   - **Never reformat lines you are not changing.**
   - **Format-scope rule.** If you run the project's formatter, scope it to the files **this change
     authored or edited** — **never** run it over a shared or pre-existing file wholesale. A
     whole-file format pass rewrites lines outside your change and reads as scope creep at review
     (revert it and the next whole-file pass just re-collapses it — a recurring loop). Whole-file
     format conformance is a **separate concern** — CI, or a dedicated chore ticket — never folded
     into this ticket's diff. This is the same surgical discipline as the untouched-lines rule
     (Principle 3), applied to the formatter, not a parallel rule.
   - Remove only orphans your change itself created; do not delete pre-existing dead code.
   - **A docstring on a tool/API surface describes DELIVERED behaviour — it IS the interface contract.**
     When the change touches a surface whose description is read by a *caller* rather than
     a maintainer — a public API/SDK docstring, a CLI `--help` string, and above all an **MCP tool
     description a client LLM reads to decide when and how to call it** — write it from **what the code
     actually does after this change**, not from what the ticket intended it to do. Name the real
     arguments, the real return shape, and the real failure/empty cases. A description that promises
     more than the code delivers is a **false-green at the interface**: the caller cannot see the code,
     so the docstring is the only thing it can be wrong about. Update it **in the same diff** as the
     behaviour it describes — a stale description left behind is a scope miss, not a follow-up.
4. **Add the proving test** named at Gate 2. Confirm it fails on the pre-change state if you can,
   then passes after the change. If it keeps failing, the two **Escalations** below apply — do not
   loop indefinitely and do not silently swap in a different approach.

   **Baseline-aware Definition of Done (detect-not-assume).** Honour the `BASELINE:` recorded at
   analysis. When `baseline: green`, the DoD is the usual "the verification command passes". When
   `baseline: red | flaky`, the DoD is **prove the delta is green**: your change must **not introduce
   any new failure**, and must **fix any pre-existing failure it claims to**. A pre-existing failure
   **outside** the change stays a **recorded baseline exclusion** — it is neither a blocker for this
   ticket nor a silent pass. Do not improvise a "baseline red, my delta green" story ad hoc; read it
   from the recorded baseline and prove your diff against it.

   **A changed golden is a BEHAVIOUR CHANGE, not a number to bump.** When a golden / snapshot /
   approved-output test goes red, **do not reflexively re-record the golden to match the new output.**
   Establish which of two things happened: the change **intentionally** altered that output — then the
   old→new delta **is a behaviour change**: state it explicitly, trace it to the approved Gate-2 change
   list, and have it **ratified at the next gate** before the golden is updated — or it altered the
   output **unintentionally**, in which case it is a **defect in the change** and the fix is the code,
   never the golden. Record the old→new delta in the working doc either way, and if the intentional
   change is **outside** the approved change list, record it as a deviation rather than absorbing it.
   Re-recording a golden silently makes the test agree with whatever the code now does — which retires
   the one assertion that would have caught the regression.
5. **Verification sweep — scope discipline on BOTH axes.** Scope discipline is measured on **two
   axes**: the **file set** AND **conformance to the approved design behaviour**. A clean file diff
   does **not** certify behavioural conformance.
   - **Axis 1 — file set.** Prove:
     - zero stray references introduced (no dangling symbols/imports from the edit);
     - the diff ⊆ approved change list (no file outside the list, no untouched-line reformatting);
     - each diff hunk maps to a matrix row.
   - **Axis 2 — design-conformance self-check (behaviour).** Walk **each Gate-2 Approach bullet**
     (not the file list) and classify it `implemented-as-approved | deviated`. Any bullet you
     implemented **differently** from what Gate 2 approved is `deviated` — **even when every touched
     file is inside the change-list**, so the Axis-1 sweep passes clean. A `deviated` bullet **must
     be recorded as a deviation** (reuse the Phase-3 deviation-record mechanism in the working doc),
     with its trace to the approved bullet, and **surfaced to review** for adjudication — exactly as
     a file-scope deviation would be. Do **not** let a green Axis-1 diff (`diff ⊆ list ✅`) sit over a
     behaviour that diverges from the approved design; and never self-mark a feature `✅` that you did
     not actually implement.
   Record **both** axes' results in the working doc.

   **Record the EMPIRICAL OUTPUT, not a prose description of it.** Every claim in this step that rests
   on having run something — the proving test, `config.test_command`, the scope greps, a typecheck, a
   lint — is recorded by **pasting the actual command and its actual output** (trimmed to the relevant
   lines, never re-typed or paraphrased) into the working doc, beside the command that produced it.
   "Tests pass" / "the sweep is clean" / "no stray references" written as prose is **not** a record —
   prose can promise more than the code delivered, a real paste cannot. **If you did not run it, say
   so** and mark the claim unproven rather than describing an outcome you did not observe. The same
   holds for a command that **failed**: paste the failure verbatim, never a summary of it.
   If the realized diff **materially exceeds** the
   approved change list or the declared `SCOPE` has crossed up a tier (S/M → L), do not absorb it —
   surface the *outgrew-its-ticket* nudge at the next gate (review) so the human can re-scope or
   split, and flag any branch/PR-type drift.
6. **Commit per logical unit — and commit the change-set BEFORE review is dispatched (binding).** One
   commit per logical unit, clear messages, **no AI co-author trailer of any kind**. The change-set is
   **committed before review dispatch**, never left uncommitted for the reviewer to find: review's
   subagents inspect the branch **ref-based** (`git diff <base>..<branch>`), and an uncommitted change-set
   makes that range **empty** — which reads as "no changes" and nearly rubber-stamps a real diff. Commit
   first so a **real committed diff exists** for the ref-based review; only bookkeeping still-in-flight
   (the working doc's Phase-4 slot) may remain uncommitted at dispatch.
7. **Write back + flow to review.** Write Phase 3 **complete on disk** into the working doc (including
   the sweep result and `Ph3/4 proven by` progress), update `Session status`, then flow straight into
   the `review` phase. When reporting this write-back into the conversation, emit only the **delta** —
   the changed rows/cells, "working doc **unchanged except** Phase 3" — not a full reprint of the doc
   (see `solve`'s response-token discipline). Do not perform any outward action (no push, no PR, no
   tracker write).

## Frontend track (only when `config.track` includes frontend)

When TRACK includes frontend, **READ `<mango>/skills/execute/frontend.md` **and** `<mango>/principles/frontend-track.md` NOW** — before implementing
the change list — and apply every rule in it: token-first (no scattered hardcoded hex/px), Pointer
Events with no hover-only affordance, compose-never-own the aesthetic, the elastic-tier
surface-coverage **proof manifest** (`PASS(automated)` → `PASS(render@<bp>)` → `EXCLUDED`), and **one
assertion per clause** of a multi-clause M-gate. **Never silently skip a surface.** This is a
**mandatory read**, not a consult-if-relevant. If `<mango>` does not resolve, say so and still emit a
manifest row per (AC × surface) at the highest tier reachable — a missing companion never turns a
required proof into no proof. On `track=backend` this section is inert.

## Escalations (mandatory STOP conditions)

These interrupt the autonomous flow. Both record the finding in the working doc before stopping.

- **Design invalidated → re-gate.** Trigger: a test (or the proving test itself) reveals the
  approved **Gate-2 approach cannot work as designed** — not a bug in your edit, but the design's
  premise being false. Action: **STOP execute. Do NOT silently invent a replacement approach and do
  NOT continue with a known-broken one.** Record the finding (with `path:line` / the test signature)
  in the working doc's Phase-3 *Design-invalidation* slot, surface the options to the user, and
  **re-open Gate 2** with a revised approach — which must re-pass design's **Assumptions** check and
  **verification plan** (A + B).
- **Stuck-detector / circuit-breaker.** After **K** failed attempts against the **same** proving
  artifact / same failing-test signature (default `K=3`, configurable as `config.stuck_threshold`
  in `.harness.json`), **STOP and escalate to the user** with a summary of what was tried and the
  options — instead of continuing. The counter **resets when the failing signature changes** (a new
  error means real progress).
