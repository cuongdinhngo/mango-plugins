## The refine phase — expose the decisions, never author the intent

> **refine (Phase 0, the FIRST phase) turns a raw request into a refined ticket by EXPOSING the
> product-decisions for the human to decide — it never authors intent. This is the same
> descriptive/normative boundary `codify` holds for rules, applied to a ticket: derivable = refine may
> resolve + cite; intent = the human's alone.**

The lifecycle now begins with `refine`:

```
refine → analysis → design → execute → review → finalize                        (ticket path)
refine → analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles        (epic path)
```

- **Scan, don't ask what the scan can answer.** refine first scans the project (reusing
  `sitemap`/`db-map`); depth of exposure comes from the scan, not from asking the user what convention
  or code already answers.
- **Premise before investigation — `PREMISE FALSIFIED` halts, it does not dig.** The first thing the
  scan does is resolve every source the ticket references **as already existing** (path, file, symbol,
  config key, table). Only a **resolvable identifier** counts — something a grep can decide; a
  **prose noun** describing behaviour ("the dashboard banner") is **ambiguous**, never a falsified
  premise. A
  reference the ticket frames as **to-be-created** never counts as missing, and an **ambiguous** one is
  **surfaced, never blocking**. A referenced-as-existing source that does not
  resolve (and is not declared synthetic) emits the counted
  `PREMISE FALSIFIED: <n> … missing — <ref>` and **STOPS for the human immediately** — no hunting for a
  renamed equivalent, no history reconstruction, no guessing what the ticket meant. Every run emits
  `PREMISE: <r> reference(s) checked | <m> missing | <a> ambiguous (surfaced, not blocking)`,
  zero included, so the check cannot silently not-happen. Enforced at `refine` (Step 0) and `analysis` (step 1, when refine did not run).
- **The readiness gate is the count itself.** refine TRIES to expose the unresolved product-decisions;
  **0 → skip → analysis** (recorded), **≥1 → refine works**, **when in doubt → run**. refine
  **self-skips on a clear ticket** so it is never a tax on every ticket — the skip is a counted
  decision.
- **The derivable/intent boundary — classify before asking.** Every surfaced decision is either
  a **how-decision (HOW)** — answerable from convention / code / the rule book / the ticket text, or a
  tool choice → refine **resolves it and CITES** the source, and **does not ask**; asking a
  HOW-question launders a decision (an **uncited** how-decision resolution is itself a finding) — or a
  **want-decision (WANT)** — intent/priority/stakes/a genuinely new choice → refine **asks the user** in
  want-language, via the **host's typed question UI** if it has one (`AskUserQuestion`'s typed fork on
  Claude Code) and otherwise as **numbered options in plain chat** — no single host tool is assumed, and
  a missing one never cancels the question. **Tie-breaker: a decision about the acceptance BAR
  itself (what counts as done / a threshold / a sourcing standard) is a want-decision by default, even
  when it looks derivable — the user owns the bar.** A handed-back want-decision **must** be marked
  **`ASSUMED (awaiting ratification)`** (reusing `codify`'s provisional→ratify; recording it as settled
  prose is a finding) and requires an **explicit next-gate confirm** before it counts as ratified —
  never silent-adopted; a tripwire fires if it would reverse a prior human decision.
- **Direction, not tool.** refine stops at solution DIRECTIONS a non-technical user can feel; the
  specific tool/library is analysis's job.
- **Every decision is a counted artifact.** The refined ticket (settled wants / cited / ASSUMED / constraints)
  and the `REFINE:` counting line are emitted, not prose — visible and challengeable at Gate 1.
- **Backstop = 1-dispatch exposure-checker, NOT a debate — on BOTH paths.** The completeness-of-exposure
  check the newbie can't self-run reuses the **ticket-blind `challenger`** as an exposure-checker with
  **one** dispatch — never a Council or multi-advisor debate. **The epic path is not exempt:** refine
  dispatches the same 1-dispatch exposure-checker **before `breakdown`**, its findings surfaced for the
  human alongside the breakdown — an un-exposed decision is costliest at epic scale, so the epic path
  may never be the one that skips the backstop.

**Epic path — thin by design (only enough to split).** On an epic, `analysis(epic)`/`design(epic)` stay thin
(architecture-level, only enough to split) and `breakdown` emits a **counted** ticket list with a
per-ticket **INVEST** self-check, **human-approved before any ticket executes** (the human holds the
gate). Ticket-boundary sizing has no exact metric; INVEST is the heuristic and **retro corrects
mis-splits**. Two epic-path invariants back the split gate: (1) a **ratified breakdown is a living
plan** — if the ticket list changes after the split-gate (a ticket added/removed, or a ratified
decision reversed/re-pointed), `breakdown` **re-ratifies** by surfacing the **delta** as a counted
artifact for an explicit human **re-approve**, never letting the change ride in on a child's Gate 1
(**Experimental** — refined by retro; see the Maturity section above); (2) after the split ratifies, the epic **scaffold**
(child stubs + BACKLOG) is **committed to a shared ref before any child ticket branches**, so a child's
edit reads as an edit of a committed file — preserving the ticket-blind challenger's net-new-vs-edit
evidence.

Enforced at `refine` (the scan, the want-decision/how-decision classification + the acceptance-bar
tie-breaker + citation, the mandatory `ASSUMED` marking with an explicit next-gate confirm, the
`REFINE:` count, the 1-dispatch exposure-checker) and `breakdown` (the counted ticket list + INVEST +
the human split-gate + the **scaffold-committed-before-child** commit + the **re-ratification** delta on
a changed split); guarded by `scripts/validate.py` (the refine + breakdown boundary tokens). refine
writes no code and no tracker entry.
