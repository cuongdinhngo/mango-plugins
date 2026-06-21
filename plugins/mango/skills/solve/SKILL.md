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

## Preflight (fail-fast)

Before starting the pipeline, run the `doctor` checks against `${CLAUDE_PROJECT_DIR}/.harness.json`.
**Refuse to start** while any ❌ remains — name exactly what to fix (point the user at `/mango:doctor`
and `/mango:init`). No partial run on a broken config.

## Order

Run, in strict order, holding the gate at each step. After analysis declares `TIER`, **honour it**:

- **`TIER: lite`** → route the rest of the work through the `quick` skill (single combined pre-code
  gate → execute → reviewer-only check → final gate). No challenger, no full matrix, no fan-out.
- **`TIER: full`** → the existing five-phase flow below.

A user may invoke `/mango:quick <KEY>` directly to force the lite lane.

1. `analysis` → **Gate 1** (and Gate 0 if `j > 0`) — STOP for approval; declares `TIER`.
2. `design` → **Gate 2** — STOP for approval.
3. `execute` → Phase 3 (autonomous) → flows into review.
   - **`execute → (design-invalidated) → design re-gate`:** if execute hits its *design-invalidated*
     escalation (a test proves the approved Gate-2 approach cannot work), it STOPS instead of
     flowing to review. Surface the options, then **re-open Gate 2** with a revised approach (which
     must re-pass design's Assumptions check and verification plan) before any further execute. Never
     continue with a known-broken approach.
   - **stuck-detector:** if execute hits `config.stuck_threshold` failed attempts at the same
     failing signature, it STOPS and escalates to the user rather than retrying further.
4. `review` → **Gate 4** — STOP only if not clean; loop back as needed.
5. `finalise` → **final gate** — STOP; one separate approval per outward action. Always captures a
   **durable lesson** (independent of deferred rows) to `config.lessons_path`.

**Resume** from the working-doc (`<config.work_dir>/<KEY>.work.md`) `Session status` block: read it,
determine the current phase, and continue from there rather than restarting. The working doc is
**separate** from the ticket spec — never appended to the raw ticket.

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
