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
   outward action**, enforce the stale-review guard: read the `Reviewed at <sha>` marker recorded at
   review and compare the current `HEAD` (and the working-tree diff) against it. If commits landed
   after that SHA, or files changed **beyond** the reviewed set, the review is **stale** — **refuse**
   to finalise / open a PR and route back to `review` for a **re-review** covering the new diff. A
   bare "go" does **not** override a stale review; only a fresh clean review (a new `Reviewed at`
   marker covering the current tree) clears it.
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
   & rollback, reviewer checklist). Do not paste raw commit messages.
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
9. **Update `Session status`** with a concrete next action (never "continue") and state the
   **revert path** (branch, commits, how to undo a merge/transition).
