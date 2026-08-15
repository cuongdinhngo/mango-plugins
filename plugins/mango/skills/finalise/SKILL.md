---
name: finalise
description: Phase 5 of the mango ticket lifecycle. Use after review is clean. Drafts the PR body from the template, lists every outward action, and requires a separate explicit approval per action. Dry-run by default. All tracker writes go through config.tracker.cli, never MCP.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — **more than one hit → take the HIGHEST `version` in its `plugin.json`
(semver compare, never `find` order, never a lexicographic sort) and report the candidate count** —
never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This phase enforces principle 4 (Goal-driven)
by recording the proving-test result in the PR and refusing any outward action without explicit,
per-action approval.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`<mango>/config/harness.example.json`. **Dry-run is the default.** Every tracker WRITE
goes through `config.tracker.cli` — **never** an MCP.

## Steps

1. **Confirm review was clean — and not stale (stale-review guard).** Read the working doc
   `<config.work_dir>/<KEY>.work.md`. If Phase 4 is not clean, return to review. Then, **before any
   outward action**, enforce the stale-review guard **mechanically** — it is a *file-set* test, never
   a commit-**count** test:
   - **Compute the changed set:** `git diff --name-only <Reviewed-at-sha>..HEAD` (the SHA from the
     `Reviewed at <sha>` marker recorded at review), unioned with any uncommitted working-tree diff.
   - **Exempt the working-doc / bookkeeping path(s)** from that set: the marker-bearing working doc
     (the separate `<config.work_dir>/<KEY>.work.md`, or — when `config.work_doc_mode` embeds it — the
     local ticket file the doc is appended to; take the exact path recorded with the marker) plus any
     file mango itself writes as bookkeeping (e.g. `config.lessons_path`). These are derived
     **deterministically** from config + the marker record, **not** by judgement, and **never** count
     toward staleness.
   - **Stale iff** any *remaining* (non-exempt) file is **beyond the reviewed set** (outside the
     reviewed file list). Then **refuse** to finalise / open a PR, take **no** outward action, and
     route back to `review` for a **re-review**, naming the unreviewed delta. A bare "go" does **not**
     clear a stale review; only a fresh clean review (a new `Reviewed at` marker covering the current
     tree) clears it.
   - If the remaining (non-exempt) set is **empty** → the review is **not stale** → **proceed**.

   The marker commit that records `Reviewed at <sha>` necessarily lands *after* the SHA it names, so
   commit *count* is never the criterion — only the **non-exempt changed file set beyond the reviewed
   set** is. Do not refuse on the marker/bookkeeping bump alone.
2. **Project finalise-checklist hook (if configured).** If `config.pr_checklist_path` is set, read
   that file **before** drafting the PR body. It is a project-owned checklist (e.g. a PR-template,
   a definition-of-done file) holding ship-time requirements mango cannot know in advance. **Walk
   each checklist item** and report it as **satisfied / not-satisfied / N-A**, each with concrete
   evidence (`path:line`, the proving-test result, a matrix row). Surface every **not-satisfied**
   item to the human at the final gate (step 6) before any outward action. mango supplies only the
   *mechanism* — the project supplies the *content*; bake no project-specific items into this skill.
   If the key is unset, skip this step and behave exactly as before.
3. **Durable lesson — ask on EVERY run, independent of deferred rows.** **This step and every one of
   `3a`–`3e` runs BEFORE the PR body and the outward-action list (steps 4–5). Do not defer any part of
   it past step 4, and do not begin step 4 until `3a`–`3e` have emitted their counting lines.** Ask:
   *"did this run produce
   a durable lesson — a constraint discovered, a wrong assumption, or a process gap?"* This is
   **not** tied to deferred (⚠) rows: a run with zero deferred rows can still have learned something
   that must outlive it. If yes, write the lesson to `config.lessons_path` (and the working doc's
   *Durable lesson* slot) as a **repo artifact** — never only to personal/assistant memory.

   **The durable lesson must land on a shared ref, not only a local branch.** A lesson (or BACKLOG entry)
   committed to a branch that finalise never offers to push is **orphaned** — a merge that deletes the
   branch takes the lesson with it, so it never reaches `main` and is not a repo artifact at all.
   So the durable-lesson / bookkeeping write must reach a **shared ref** by **one** of two routes:
   **either** fold it into a commit the approved **branch-push**
   (step 5) already carries **before** PR-open, **or** enumerate an explicit **"push bookkeeping"
   outward action** at the final gate — taken under the **same per-action approval + idempotency check**
   as every other outward action. Never let the durable lesson depend on a commit finalise never offered
   to push.

   ### 3a. Split the lesson into atomic CLAIMS (the unit of everything below)

   **READ `<mango>/principles/learning-loop.md` NOW, before step 3a runs.** It carries the six claim
   types, both tiebreaks, and the five invariants every step from 3a to 3e applies. The read is
   unconditional, not consult-if-relevant. If `<mango>` does not resolve, say so and classify against
   the six types named inline in 3b/3e rather than dropping the classification to prose.

   A captured lesson is frequently **bundled** — a tool fact, a principle, and a project fact in one
   paragraph. **Split it into atomic claims first**, each one falsifiable sentence, and write each in the
   shape of `<mango>/templates/claim-record.md`. Every step below operates on the
   **claim**, never the entry. Emit the counted artifact:

   `CLAIMS: <c> claim(s) from <e> lesson entr(ies) | T1=<n> T2=<n> T3=<n> T4=<n> T5=<n> T6=<n> | <u> unclassified`

   A bundled entry left whole is a **finding at this step**: `<c>` must cover every claim the entry
   carries, and `<u>` must reach 0 before the gate.

   ### 3b. Classify each claim — PROPOSE the type, the human confirms

   Tag each claim with **type + evidence + its recall handle**, per the six-type table and the two
   tiebreaks in `<mango>/PRINCIPLES.md` (The learning loop). Type 1 carries a
   `handle: symbol:<import/API>`; **type 2 carries a `handle: <class-slug>`** — a short kebab-case slug
   naming the CLASS of heuristic (e.g. `blast-radius-grep`), never a symbol and never an area, because a
   heuristic holds across tools; a type-2 claim with **no** `handle:` is a **finding at this step** (it is
   unrecallable, so it cannot reach the next ticket); type 5 carries an `area:` (**not** a symbol) plus its sub-shape
   (descriptive / normative / environment, the environment shape carrying `verified-at:`); type 6 carries
   the `re-raise:` finding **and a mandatory `expiry:`**. Apply the tiebreaks **during** classification:
   **1 vs 4** — an imaginable gate makes it type 1, only a claim no gate could ever pre-empt is type 4;
   **2 vs 3** — type 3 **only** when a phase demonstrably skipped a doable check **in this run**, else
   the general principle is type 2, and a **preventive** process-lesson with nothing skipped routes to
   `config.agent_brief_path` rather than a rule.

   Every classification is a **PROPOSAL**: it is `status: proposed (awaiting human confirm)` until the
   human confirms it at the final gate (step 6). Do **not** classify-and-act.

   ### 3c. Recurrence + supersession (dedup across entries)

   Read the existing claims in `config.lessons_path` and dedup this run's claims against them:
   - a claim already recorded and **seen again** → append this ticket key to its `seen:` list and flag it
     a **promotion candidate** (it recurred *despite* being written down, so recording it was not
     enough);
   - a claim that **narrows or falsifies** an earlier one → it **REPLACES** it: record `supersedes:` on
     the new claim and mark the old one `retired: … superseded by <CLAIM-ID>`. Retiring **never deletes**
     the old record — recall skips it, history stays.

   `RECURRENCE: <n> recurring | <s> superseded (<r> retired) | <p> promotion candidate(s)`

   ### 3d. ⭐ Falsification gate — BEFORE the ratification gate, never after

   Recurrence measures how often a claim was **RESTATED**, not whether it was ever **CHECKED**. So every
   promotion candidate from 3c faces a falsification check **before** it is proposed to the human:

   1. **Is it still true?** Check it against the current checkout / tool / environment — do not accept
      the claim's own restatements as evidence.
   2. **Is it cheaply verifiable?** Name the grep, command, or test that would disprove it.
   3. **Was it CHECKED, or only repeated?** Count the sightings that carry real evidence, not the
      sightings.

   A candidate that is **falsified**, or that **cannot be cheaply checked**, is **BLOCKED from
   promotion** — it stays a recorded claim (a falsified one is marked `retired: falsified …`), and it
   never reaches the ratification gate. Only a candidate that passes all three is proposed in 3e.

   `FALSIFY: <c> candidate(s) checked | <t> still-true (proceed) | <f> falsified (BLOCKED) | <u> not cheaply checkable (BLOCKED)`

   ### 3e. Promotion — PROPOSE the destination; the human ratifies; every destination is a PROJECT file

   For each candidate that survived 3d, **propose** its destination from its type — never write first:
   - **type 2 (code)** and **type 5-normative** → `config.rulebook_path`, through `codify`'s
     provisional→ratify flow (reuse it; invent no parallel one). A type-5-normative entry carries an
     **ID + blocking status**.
   - **type 2 (process)** and any preventive process-lesson → `config.agent_brief_path`. **Never file a
     process claim in the code rule book.**
   - **type 4** → `config.gotchas_path`. **type 5-descriptive** → `config.design_doc_path`.
   - **type 6** → `config.drift_path`, **carrying its `expiry:` condition**.
   - **type 3 (skill-gap) does NOT promote into mango.** Record it as a **SIGNAL** in
     `config.skill_gap_path` for mango's maintainer, who changes mango only through a normal version.

   **⭐ A RECURRING type-2 claim may NOT resolve to `stays in lessons_path` (binding).** When a claim is
   **type 2** and its `seen:` list holds **≥ 2 ticket keys**, the destination
   `stays in lessons_path` is **rejected**: writing it down was already the treatment and the claim came
   back. It resolves to **exactly one** of:

   - `config.rulebook_path` (the claim's subject is **code**) or `config.agent_brief_path` (the subject is
     **process**) — the same subject routing as the two bullets above; **or**
   - the literal `cannot promote: <reason>` — naming **which** blocker applies: the destination key is
     **unset**, or the falsification gate (3d) **BLOCKED** it. The claim is then **surfaced** to the human
     at the gate, never silently dropped and never quietly re-defaulted to `lessons_path`.

   `RECURRING-T2: <n> type-2 claim(s) with seen ≥ 2 | <d> routed to a destination | <b> cannot promote (reason) | <l> left in lessons_path`

   **`l` must be 0 and `n` must equal `d + b`; any `l > 0` BLOCKS finalise** — a recurring type-2 claim
   still reading `destination: stays in lessons_path` is incomplete exactly as a **blank ledger token
   cell** is (step 9): the check requires a real destination **or** an explicit named reason, never the
   silent default. Emit the line on every run, zeros included.

   **This rule keys on type 2 and on `seen: ≥ 2` — nothing else.** **Type 5 is untouched:** a type-5
   project/domain fact legitimately `stays in lessons_path` however often it recurs, and this rule never
   moves one. A type-2 claim seen **once** is also untouched — recurrence, not presence, is the trigger.

   **Nothing the loop does edits a mango skill, agent brief, template, or `PRINCIPLES.md`** — no lesson,
   however recurrent or ratified, modifies mango, and no loop output is ever written outside the project
   repo. If a destination key is unset, say so and surface the claim rather than silently dropping it.

   **The write happens only after an explicit per-claim ratify at the final gate (step 6).** Then:
   **the rule goes into `config.rulebook_path`, never into `CLAUDE.md`** — nor into whichever always-on
   context file the host loads (`config.context_file`, which may be `AGENTS.md`); that file carries only
   the **pointer** `init` already wrote. Create the rule book at `config.rulebook_path` if it is absent.
   A promotion is **not done** until the rule is in the rule book **and** `doctor` is green on the
   context-file → rule-book pointer; `init`/`doctor` already own that wiring — including resolving which
   file the host actually loads — so reuse it and rebuild none of it.

   `PROMOTION: <p> proposed | <k> human-ratified | destinations: <path>, … | mango files written: 0`

   **Hand a cross-ticket class to `/mango:promote`, do not attempt it here.** When a **type-2** claim's
   `seen:` list now holds **≥ 2 ticket keys**, name `/mango:promote` at the final gate as the cross-ticket
   pass the human runs **between tickets** — this phase sees only this ticket's claims and may not stand in
   for a pass over the whole corpus. Naming it is not running it: `finalise` invokes nothing.

   The `mango files written: 0` figure is not decoration — a non-zero value means the loop edited mango
   and the run is wrong.
4. **Draft the PR body.** Render `<mango>/templates/pr.md` to `/tmp/pr-<KEY>.md`.
   Derive content from the working doc (summary, changes, the proving test + result, data/DB, risk
   & rollback, reviewer checklist). Do not paste raw commit messages. When the recorded `BASELINE`
   was `red | flaky`, report the proving-test result **against that baseline** (delta-green: no new
   failure; claimed fixes landed) and note any pre-existing **baseline exclusions** — never claim a
   blanket "all green" the baseline never supported.

   **Every ran-it claim in the PR body carries the EMPIRICAL OUTPUT, not a description of it.** The
   proving-test result, the verification command, any checklist evidence: **paste the actual command
   and the actual output** `execute` recorded in the working doc (trimmed to the relevant lines,
   verbatim, never re-typed or re-summarised). A prose sentence can promise more than the run
   delivered; a real paste cannot. If the working doc holds no such output for a claim, the claim is
   **unproven** — say so in the PR body rather than narrating an outcome nobody observed, and never
   reconstruct output from memory.
5. **List planned outward actions.** Enumerate every outward action the ticket needs, e.g.:
   - push the branch;
   - **push the bookkeeping commit** carrying the durable lesson / BACKLOG to a **shared ref** — so the
     lesson is not orphaned on a soon-deleted local branch (see step 3). Fold it into the branch-push
     above when it rides the same branch; otherwise list it as its own action. Idempotent: skip if the
     shared ref already carries it;
   - open a PR via `config.pr_host`;
   - tracker comment (via `config.tracker.cli`);
   - tracker transition (via `config.tracker.cli`).
   **Frontend-track PR discipline (when `config.track` includes frontend):** do **not** mix
   aesthetic/responsive changes into a logic/backend PR — they ride a **separate branch** (per
   `config.branch_strategy`). If the diff has crossed from one into the other, surface it here as an
   *outgrew-its-ticket* split rather than shipping a mixed PR. Reuse the existing per-action approval +
   dry-run below; this adds no new outward action.
6. **Require explicit, separate approval per action.** Present the list (and any not-satisfied
   checklist items from step 2, plus every **claim classification** and **promotion proposal** from
   step 3) and **stop**. Take NO outward action until the user approves each one
   individually. Silence ≠ approval. Default to dry-run: show the exact command you would run for each.
   A step-3 classification or promotion is **ratified here, per claim, explicitly** — a blanket "go" on
   the outward actions is **not** a ratification of a claim, and an unratified claim is written nowhere.
7. **Execute only approved actions.** For each approved action, run it. All tracker writes use
   `config.tracker.cli`. After each, report what happened.
8. **Draft follow-up tickets** for every deferred (⚠) matrix row, so nothing silently drops.
9. **Cost ledger — completeness gate (content, not just row count), then the descriptive summary (dispatch-only).**
   Before surfacing the summary, enforce the **ledger-completeness check** — the ledger's *teeth*, and a
   **dispatch-count** check widened to the **content** of each row. Count the subagent dispatches this run
   actually made (knowable from the run — every `reviewer` / `challenger` / `extractor` / Explore fan-out /
   per-review-round dispatch return). The ledger is **complete** only when **both** hold: **(i)** every
   dispatch has a row (row count ≥ dispatch count), **and** **(ii)** every dispatch row carries a **token
   value** — a real count from that return's usage block **or** an explicit `unmeasured (<reason>)`
   marker (e.g. `unmeasured (blocking retrieval)`) from `solve`'s usage-surfacing step.
   **Refuse to proceed if the ledger has fewer rows than the run made dispatches OR any dispatch row
   has a blank/absent token cell:** a missing row
   **or** a blank token value is an **incomplete** ledger and **blocks finalise exactly as an unfilled
   matrix column blocks a gate** — name the missing dispatches / blank cells and require each to be
   transcribed from its return's usage block (or marked `unmeasured (blocking retrieval)`) before
   continuing. **A ledger whose rows all read `unmeasured (host does not surface usage)` is COMPLETE and
   passes** — on a host that surfaces no usage block, that marker is the expected and correct value, and
   the gate checks the *presence* of an honest value, never that a number was obtained. **Never invent,
   estimate, or back-fill a number to clear this gate** — a fabricated count is a false-green and worse
   than an honest `unmeasured`. This checks **ledger completeness** — the *presence* of a value or an honest marker in
   every row — and stays **descriptive**: it never **inspects, judges, ranks, invents, or auto-cuts** a
   row, and the gate never cuts a check, a critic, or evidence. A ledger with a row per dispatch and a
   value (or the explicit marker) in every token cell proceeds. Then read the working-doc **Cost
   ledger** and print a one-line summary — `LEDGER TOTAL: <tokens> · top cost driver: <phase/subagent>`
   — at the final gate, plus any recorded optimizer saving. This is **facts only**: it makes the cost
   visible so a human can decide where to trim; it **never** triggers an automatic cut of a check, a
   gate, a critic, or evidence detail. It is also the data a later middle-tier sizing decision needs —
   measure before you size. **State the scope honestly:** the ledger measures **subagent dispatch
   only** — main-loop output noise (verbose lint/test/build dumps, file reads) is **not measured by
   mango**. Do **not** fabricate or imply a dispatch-vs-noise split (a 100%-dispatch / 0%-noise number
   is an instrumentation artifact, not a finding). For the output-noise side, point the user at the
   optimizer's own analytics — **`rtk gain`** when RTK is live — rather than having mango self-instrument
   the main loop; each layer measures its own domain. When surfacing the ledger into the conversation,
   print only the **delta** plus the summary line — a new row, "ledger **unchanged except** row N" —
   never a full reprint of the whole ledger on each update; the completeness gate reads the ledger
   **complete on disk**, not a re-pasted copy in the response.
10. **Update `Session status`** with a concrete next action (never "continue") and state the
   **revert path** (branch, commits, how to undo a merge/transition).
11. **Learning-loop self-check.** Before finishing, confirm each: steps `3a`–`3e` ran **before** the PR
    body and the outward-action list (steps 4–5), not after; every lesson entry was **split** into
    atomic claims and `<u> unclassified` is 0; **every type-2 claim carries a `handle:`** and every type-2
    claim with `seen: ≥ 2` resolved to a destination or an explicit `cannot promote: <reason>` (the
    `RECURRING-T2:` line's `<l>` is 0); every classification is a **proposal** the human
    confirmed; **falsification ran before** the ratification gate and every falsified / not-cheaply-checkable
    candidate is **BLOCKED** from promotion; every ratified promotion landed in a **PROJECT** path (the
    rule in `config.rulebook_path`, **not** copied into `CLAUDE.md`) with `doctor` green on the pointer;
    every type-3 claim went to `config.skill_gap_path` as a signal and **no mango file was written**; and
    all six counting lines (`CLAIMS:`, `RECURRENCE:`, `FALSIFY:`, `RECURRING-T2:`, `PROMOTION:` and the
    durable-lesson record) are emitted.
