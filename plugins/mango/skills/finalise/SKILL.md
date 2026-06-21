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

1. **Confirm review was clean.** Read the working doc `<config.work_dir>/<KEY>.work.md`. If Phase 4
   is not clean, return to review.
2. **Draft the PR body.** Render `${CLAUDE_PLUGIN_ROOT}/templates/pr.md` to `/tmp/pr-<KEY>.md`.
   Derive content from the working doc (summary, changes, the proving test + result, data/DB, risk
   & rollback, reviewer checklist). Do not paste raw commit messages.
3. **List planned outward actions.** Enumerate every outward action the ticket needs, e.g.:
   - push the branch;
   - open a PR via `config.pr_host`;
   - tracker comment (via `config.tracker.cli`);
   - tracker transition (via `config.tracker.cli`).
4. **Require explicit, separate approval per action.** Present the list and **stop**. Take NO
   outward action until the user approves each one individually. Silence ≠ approval. Default to
   dry-run: show the exact command you would run for each.
5. **Execute only approved actions.** For each approved action, run it. All tracker writes use
   `config.tracker.cli`. After each, report what happened.
6. **Draft follow-up tickets** for every deferred (⚠) matrix row, so nothing silently drops.
7. **Durable lesson — ask on EVERY run, independent of deferred rows.** Ask: *"did this run produce
   a durable lesson — a constraint discovered, a wrong assumption, or a process gap?"* This is
   **not** tied to deferred (⚠) rows: a run with zero deferred rows can still have learned something
   that must outlive it. If yes, write the lesson to `config.lessons_path` (and the working doc's
   *Durable lesson* slot) as a **repo artifact** — never only to personal/assistant memory. (Observed
   failure: a run discovered a durable constraint — two live rich-text editors corrupt each other —
   but had no deferred rows, so it nearly never reached the repo's shared `LESSONS.md`.)
8. **Update `Session status`** with a concrete next action (never "continue") and state the
   **revert path** (branch, commits, how to undo a merge/transition).
