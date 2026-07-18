---
name: breakdown
description: Epic-only phase of the mango lifecycle — runs ONLY on the epic path, AFTER design(epic). Splits an epic into tickets using the epic-level architecture, emits a counted ticket list with a per-ticket INVEST self-check, and holds a human gate before any ticket executes. Each resulting ticket then runs its own full lifecycle. Deliberately thin — v1, expected to be refined by retro.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. `breakdown` is **not** part of the single-ticket
lifecycle — it activates **only on the epic path**, **after `design(epic)`**, when `refine` detected an
epic. Its job is to draw **ticket boundaries** from the epic-level architecture so each resulting ticket
can run its own full lifecycle (`analysis → design → execute → review → finalize`).

> ⚠️ **This is v1 — "enough to run and learn".** The exact epic→ticket boundary sizing has **no exact
> metric** (no agile method provides one). INVEST is the heuristic here; **retro corrects mis-splits.**
> Keep this phase thin: enough to split, not more. If a retro later shows a *technique* gap in how to
> split, consider adding SPIDR — **not now.**

**Ground rules.** Read `${CLAUDE_PROJECT_DIR}/.harness.json` first. If it is missing, STOP and tell the
user to create one from `${CLAUDE_PLUGIN_ROOT}/config/harness.example.json`. `breakdown` writes **no
code** and makes **no tracker write**; it emits a counted ticket list into the working doc and stops at
its human gate.

## Steps

1. **Read the epic architecture.** Take the DIRECTION vetted by `analysis(epic)` and the module/layer
   map from `design(epic)` — thin, architecture-level, **only enough to draw ticket boundaries** (never
   line-level design).
2. **Split into tickets.** Draw each ticket's **ticket boundary** from that architecture so every
   ticket is an independent, execute-able deliverable.
3. **Per-ticket INVEST self-check — ENUMERATED, not a one-liner.** For **each** proposed ticket,
   **enumerate all six** INVEST criteria and check each one — Independent, Negotiable, Valuable,
   Estimable, Small, Testable. Each letter is **either affirmed with a
   one-clause reason or marked `N/A` with a reason** — never a single descriptive sentence labelled
   "INVEST" (a nominal one-liner is INVEST theatre; it cannot catch a boundary problem). This mirrors
   the exact *"enumerate every applicable item and check it"* discipline analysis applies to its
   rulebook-section coverage. Small / Testable / Independent are already mango language (right-sizing,
   the proving test, the clean execute boundary), so reuse those — do not invent a parallel vocabulary.
   **A ticket that fails a letter is a breakdown finding** — e.g. not **S**mall (too big) or not
   **I**ndependent (entangled with another ticket): **re-split before ratification**, do not carry it
   to the gate as-is.
4. **Emit the ticket list as a counted artifact.** The output is a **counted** ticket list (each row:
   proposed key, one-line scope, the **six-letter enumerated** INVEST self-check — one clause per
   letter). Emit the counting line:

   `BREAKDOWN: <N> tickets proposed | <N> INVEST self-checks emitted (6 letters each) | <f> tickets flagged for re-split`

5. **✋ Human gate — the split is proposed, the human ratifies.** `breakdown` **proposes** the split;
   the human **holds the gate** and approves the ticket list **before any ticket executes.** No ticket
   from an unratified breakdown may enter execute. Silence ≠ approval.
6. **Hand off.** On approval, each ticket runs its **own full lifecycle** (one ticket per run). Record
   the approved list + the gate decision in the working doc.

> ⚠️ **Boundary sizing has no exact metric** — INVEST is the heuristic, retro corrects mis-splits.
> Because this whole phase is **v1-learning**, expect a retro to refine both the epic-level
> analysis/design boundary and this breakdown's sizing.
