---
name: quick
description: The lite lane of the mango lifecycle, for trivial tickets (SCOPE=S, single file/row, no universal requirement, not security-tagged). Use to ship a one-line fix without the full five gates — a single combined pre-code gate, then execute, a reviewer-only check, and the final gate. Skips the full matrix, challenger, and fan-out.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This is the right-sized lane: it still enforces
surgical changes (diff ⊆ approved change) and goal-driven execution (a green **proving test**), but
drops the ceremony that a trivial ticket does not need.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` and ground rules in
`config.rulebook_path`. If `.harness.json` is missing, STOP and tell the user to create one from
`${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. Use only on a ticket that qualifies for
`TIER: lite` (SCOPE=S, single file / single requirement row, no universal "all/every/no"
requirement, not security-tagged). If it does not qualify, route to `solve` (full tier) instead.
**The lite lane always skips fan-out** regardless of `config.explore_fanout`, and **runs on a single
model** — no delegation overhead (see `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`).

## Steps

0. **Hard entry check (REFUSE non-qualifying tickets).** Before anything else, confirm the ticket is
   genuinely trivial. **STOP and route the user to `/mango:solve` (full tier)** — do not proceed — if
   ANY of these hold:
   - the ticket is **security-tagged**;
   - the change touches **more than one file**;
   - the ticket contains a **universal ("all/every/no") requirement that resolves to N > 1** — judged
     on the resolved inventory denominator N, **not** on the wording alone. A requirement that sounds
     universal but resolves to **N = 1** (a single affected site) does **not** disqualify the ticket.
   This is a refusal, not a "should": lite exists only for single-file, single-requirement,
   non-security fixes. A direct `/mango:quick <KEY>` on a ticket that fails this check is rejected
   here.
1. **Minimal working doc.** Create the working doc `<config.work_dir>/<KEY>.work.md` (default
   `work_dir` = `tickets_dir`) from the template — a **separate file** from the ticket spec, never
   appended to the raw ticket — but fill only the **single goal row**, the **one change**, and the
   **proving test**. Set `TIER: lite`.
2. **Single combined gate (✋).** Present, together, the one change AND the proving test, and STOP
   for one approval before any code. This is the lite lane's **single combined gate** — there is no
   separate design gate. Silence ≠ approval.
3. **Execute.** On an approved branch, make ONLY that change; match surrounding style; never
   reformat untouched lines. Add the proving test. Run the **surgical/diff-scope check**: the diff
   must be ⊆ the approved change. Commit (no AI co-author trailer).
4. **Reviewer-only check.** Run the `reviewer` agent on the diff. **No challenger, no full matrix.**
   Confirm the proving test is green via `config.test_command`. If the reviewer reports Critical or
   the test is red, loop back and STOP. **Stuck-detector:** after **K** failed attempts against the
   same proving artifact / same failing-test signature (default `K=3`, configurable as
   `config.stuck_threshold` in `.harness.json`), STOP and escalate to the user with what was tried
   and the options instead of retrying further; the counter resets when the failing signature
   changes.
5. **Finalise.** Hand off to `finalise`'s final gate: dry-run by default, one separate approval per
   outward action. Update `Session status` with a concrete next action.

**Two human gates total:** the combined pre-code gate and the final gate.
