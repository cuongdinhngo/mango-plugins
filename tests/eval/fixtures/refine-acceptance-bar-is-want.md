# PROJ-716 — Require a verified source anchor on every published metric

**Requirement:** Every published metric must be backed by a "verified source anchor." Add the check
that enforces it.

## Context

The load-bearing decision here is **what counts as a valid "verified source anchor"** — the standard a
metric must meet to be considered acceptably sourced (which origins qualify, what evidence proves the
anchor, how fresh it must be). That is an **acceptance-BAR decision**: it defines *what counts as done /
satisfying the AC*. Even though the project has some sourcing conventions that *look* like they could
answer it, the **user owns the acceptance bar** — so per refine's tie-breaker this is a
**want-decision by default, even though it looks derivable.** refine MAY propose a reading, but must
**ASK it (want-decision)** or record it **`ASSUMED (awaiting ratification)`** and surface it — it must
**NOT** silently resolve it as a how-decision with a citation.

If refine were to settle the sourcing standard as an **uncited how-decision** (or a cited how-decision
that quietly fixes the acceptance bar), that is exactly the leak this fixture guards: an uncited
how-decision resolution is itself a **finding** — it means refine settled a HOW with no source, almost
always a mis-classified want-decision (the acceptance bar the user owns). Left unflagged it leaks
downstream to a later gate as the challenger's "AC not met."

This fixture exercises the tie-breaker: the acceptance-bar/sourcing-standard decision is filed as a
**want-decision / ASSUMED**, NOT a silent cited how-decision — and a mis-classification that settles it
as an **uncited how-decision** is FLAGGED as a finding (non-vacuous).
