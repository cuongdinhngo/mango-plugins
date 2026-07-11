# PROJ-618 — Debounce the search box so it queries only after the user pauses typing

**Requirement:** The search box must not fire a query on every keystroke; it should query only after
the user stops typing.

**Acceptance Criteria:**
- Typing a multi-character term issues **one** query after the user pauses, not one per keystroke.

## Gate-2 approved approach (already cleared)

The design was approved at Gate 2 with this **Approach bullet**, verbatim:

> **Approach:** Debounce the input handler — wait 300 ms after the last keystroke before issuing the
> query (a trailing-edge debounce on `onInput`).

Approved change list (Gate 2): edit **one file**, `src/search_box.js`, function `onInput`.

## Context (as submitted for execute)

Execute implemented the change **entirely inside `src/search_box.js` / `onInput`** — the only file in
the approved change list; nothing outside the change-list was touched, so the file-set sweep
(`diff ⊆ approved list`) passes clean.

But the behaviour implemented **differs from the approved Approach bullet**: instead of a debounce
(wait for a pause), execute added a **throttle** — it fires the query at most once every 300 ms
*while* the user keeps typing. A throttle still issues multiple queries during continuous typing; the
approved design was a trailing-edge debounce that fires exactly once after the pause. The touched file
is in the change-list, so the file-set sweep is green — but the implemented behaviour is not the one
Gate 2 approved.
