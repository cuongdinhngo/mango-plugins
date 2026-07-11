---
name: finalise
description: Phase 5 of the mango ticket lifecycle. Use after review is clean. Drafts the PR body from the template, lists every outward action, and requires a separate explicit approval per action. Dry-run by default. All tracker writes go through config.tracker.cli, never MCP.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This phase enforces principle 4 (Goal-driven)
by recording the proving-test result in the PR and refusing any outward action without explicit,
per-action approval.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground every rule in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. **Dry-run is the default.** Every tracker WRITE
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
   item to the human at the final gate (step 5) before any outward action. mango supplies only the
   *mechanism* — the project supplies the *content*; bake no project-specific items into this skill.
   If the key is unset, skip this step and behave exactly as before.
3. **Draft the PR body.** Render `${CLAUDE_PLUGIN_ROOT}/templates/pr.md` to `/tmp/pr-<KEY>.md`.
   Derive content from the working doc (summary, changes, the proving test + result, data/DB, risk
   & rollback, reviewer checklist). Do not paste raw commit messages. When the recorded `BASELINE`
   was `red | flaky`, report the proving-test result **against that baseline** (delta-green: no new
   failure; claimed fixes landed) and note any pre-existing **baseline exclusions** — never claim a
   blanket "all green" the baseline never supported.
4. **List planned outward actions.** Enumerate every outward action the ticket needs, e.g.:
   - push the branch;
   - open a PR via `config.pr_host`;
   - tracker comment (via `config.tracker.cli`);
   - tracker transition (via `config.tracker.cli`).
   **Frontend-track PR discipline (when `config.track` includes frontend):** do **not** mix
   aesthetic/responsive changes into a logic/backend PR — they ride a **separate branch** (per
   `config.branch_strategy`). If the diff has crossed from one into the other, surface it here as an
   *outgrew-its-ticket* split rather than shipping a mixed PR. Reuse the existing per-action approval +
   dry-run below; this adds no new outward action.
5. **Require explicit, separate approval per action.** Present the list (and any not-satisfied
   checklist items from step 2) and **stop**. Take NO outward action until the user approves each one
   individually. Silence ≠ approval. Default to dry-run: show the exact command you would run for each.
6. **Execute only approved actions.** For each approved action, run it. All tracker writes use
   `config.tracker.cli`. After each, report what happened.
7. **Draft follow-up tickets** for every deferred (⚠) matrix row, so nothing silently drops.
8. **Durable lesson — ask on EVERY run, independent of deferred rows.** Ask: *"did this run produce
   a durable lesson — a constraint discovered, a wrong assumption, or a process gap?"* This is
   **not** tied to deferred (⚠) rows: a run with zero deferred rows can still have learned something
   that must outlive it. If yes, write the lesson to `config.lessons_path` (and the working doc's
   *Durable lesson* slot) as a **repo artifact** — never only to personal/assistant memory. (Observed
   failure: a run discovered a durable constraint — two live rich-text editors corrupt each other —
   but had no deferred rows, so it nearly never reached the repo's shared `LESSONS.md`.)
9. **Surface the Cost ledger summary (descriptive).** Read the working-doc **Cost ledger** and print
   a one-line summary — `LEDGER TOTAL: <tokens> · top cost driver: <phase/subagent>` — at the final
   gate, plus any recorded optimizer saving. This is **facts only**: it makes the cost visible so a
   human can decide where to trim; it **never** triggers an automatic cut of a check, a gate, a
   critic, or evidence detail. It is also the data a later middle-tier sizing decision needs — measure
   before you size.
10. **Update `Session status`** with a concrete next action (never "continue") and state the
   **revert path** (branch, commits, how to undo a merge/transition).
