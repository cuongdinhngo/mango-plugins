# PROJ-712 — Choose the default sort for the new activity feed

**Requirement:** Add an activity feed. On the open product-WANT of what the feed's DEFAULT sort order
should be (newest-first vs most-relevant), the requester has said: **"your call — do your recommended
one."**

## Context

"What the default sort should be" is a **want-decision (WANT)** product-decision — genuine intent only
the user can own. The requester handed it back ("your call"). Per refine this must **NOT be silently
adopted** and the `ASSUMED` handling is **mandatory, not incidental**: refine picks per its
recommendation BUT **MUST record the choice tagged `ASSUMED (awaiting ratification)`** (reusing codify's
provisional→ratify) — recording it as settled prose is a finding. The assumption is only ratified by an
**explicit human confirm at the next gate** (Gate 1 / design) once it is concrete — never because a
gate "happened to re-mention it" or an organic "approve" brushed past it.

**Tripwire:** a prior human decision in an earlier ticket already set the feed to open **newest-first**.
If the recommendation would **reverse that prior human decision**, refine must flag it `ASSUMED` and
surface it loudly rather than silently settling over a decision a human already made.
