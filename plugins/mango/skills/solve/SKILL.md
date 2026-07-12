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
4. `review` → **Gate 4** — STOP only if not clean; loop back as needed. On a clean verdict, `review`
   records a `Reviewed at <sha>` marker (commit SHA + reviewed files). **Carry that reviewed SHA
   across the review→finalise transition.** If `execute` or `design` runs **again** after a clean
   review (a loop-back), the review is **stale** — drop the marker and require a fresh review before
   finalise.
5. `finalise` → **final gate** — STOP; one separate approval per outward action. **Stale-review
   guard (mechanical, file-set — never commit count):** before any outward action, finalise diffs the
   live tree against the `Reviewed at` marker, **exempts** the working doc / bookkeeping paths, and
   **refuses** the PR (routing back to `review`) iff any *remaining* source file changed **beyond the
   reviewed set** — the working-doc/marker bump alone never trips it, and a bare "go" does not override
   it. Always captures a **durable lesson** (independent of deferred rows) to `config.lessons_path`.

**Resume** from the working-doc `Session status` block: read it, determine the current phase, and
continue from there rather than restarting. The working doc's placement follows
`config.work_doc_mode` (default `auto`) — a **separate** `<config.work_dir>/<KEY>.work.md` for a
tracker-hosted ticket, or **appended below a raw-ticket separator line** inside a local-file ticket.
Either way the raw ticket portion stays above the separator and is never mixed with the design, so
the challenger payload (`review`) can always exclude the working-doc portion.

## Non-negotiables

- **Never skip or self-approve a gate.** Silence ≠ approval.
- **No outward action without explicit per-action approval.**
- **Writes via CLI, not MCP** (`config.tracker.cli`).
- **Do not widen scope.** Stay inside the approved change list.
- **"Outgrew its ticket" nudge — never auto-absorb an expansion.** Track the declared `SCOPE`/`TIER`.
  If at any gate the **realized** scope crosses **up a tier** (especially S/M → L), or the
  change-list / diff materially exceeds the approved one, **stop at the next gate** and surface that
  the card has **outgrown its original scope**. Ask the human to either formally **re-scope** (update
  the working-doc `SCOPE`, and the branch/PR type if the change type drifted from the branch type) or
  **split** the excess into a follow-up ticket. Flag any **branch/PR-type drift** (e.g. a `fix`
  branch now carrying a feature). Record the re-declaration in the Decision log. Never silently
  absorb the growth into the working doc.
- A mid-run **"do the full thing"** instruction **resets coverage to the literal ticket text**:
  re-derive every matrix row from scratch; prior deferrals expire.
- **One ticket per run.**
- **Reject any phase that reaches a gate with an unfilled matrix column.**
- **Process corrections become repo artifacts.** When the user corrects how a phase behaves, log it
  to `config.lessons_path` AND fix the offending skill/doc in the same session.
- **Emit a Cost-ledger row per dispatch return (mechanical, not narrated).** The ledger is **not**
  bookkeeping to remember "as you go" — a thing the model can silently forget (an unenforced artifact
  is a coin flip). Instead: **when a subagent dispatch returns** (reviewer, challenger, extractor,
  Explore fan-out, each review round), **append one ledger row from that return's usage block** — phase,
  dispatch name, round, tokens — as an **immediate, non-optional by-product of dispatching**. The rule
  is mechanical: **a ledger row is emitted per dispatch return; a run that dispatched N subagents ends
  with N rows.** (This is the ledger's "teeth" — not a gate that blocks, but a mechanical emission so it
  can't silently not-happen; the harness surfaces each subagent's token usage on return, so the row is
  transcribed from that, not invented.) The ledger stays **descriptive**: it records facts and never
  itself decides to cut a check, a gate, a critic, or evidence detail. It measures **subagent dispatch
  only** — main-loop output noise is **not** measured by mango (see `finalise`). `finalise` surfaces the
  one-line summary (total + top cost driver). See `/mango:budget` for the safety axis and the
  human-gated `token_optimizer` adoption; mango tolerates RTK's compact Bash output but **never depends
  on it** — RTK absent, the run is identical.
