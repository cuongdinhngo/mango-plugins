---
name: solve
description: Orchestrator for the full mango ticket lifecycle. Use to run analysis → design → execute → review → finalise in order on one ticket, holding every gate. Resumes from the working-doc Session status. This is a skill, not an agent, because gates must pause in the live conversation.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This phase orchestrates all four principles by
running each gated phase in order and refusing to cross any gate on your behalf.

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` first. If it is missing, STOP and tell
the user to create one from `${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`.

State up front, verbatim: **"I stop and wait for you at every ✋ gate."**

## Why this is a skill, not an agent

Gates require pausing in the **live conversation** so the human can approve. A subagent runs
isolated and returns once — it cannot hold a gate open, surface a Gate-0 question mid-run, or take a
per-action approval. So orchestration must live here, in-conversation, as a skill.

## Order

Run, in strict order, holding the gate at each step:

1. `analysis` → **Gate 1** (and Gate 0 if `j > 0`) — STOP for approval.
2. `design` → **Gate 2** — STOP for approval.
3. `execute` → Phase 3 (autonomous) → flows into review.
4. `review` → **Gate 4** — STOP only if not clean; loop back as needed.
5. `finalise` → **final gate** — STOP; one separate approval per outward action.

**Resume** from the working-doc `Session status` block: read it, determine the current phase, and
continue from there rather than restarting.

## Non-negotiables

- **Never skip or self-approve a gate.** Silence ≠ approval.
- **No outward action without explicit per-action approval.**
- **Writes via CLI, not MCP** (`config.tracker.cli`).
- **Do not widen scope.** Stay inside the approved change list.
- A mid-run **"do the full thing"** instruction **resets coverage to the literal ticket text**:
  re-derive every matrix row from scratch; prior deferrals expire.
- **One ticket per run.**
- **Reject any phase that reaches a gate with an unfilled matrix column.**
- **Process corrections become repo artifacts.** When the user corrects how a phase behaves, log it
  to `config.lessons_path` AND fix the offending skill/doc in the same session.
