# PROJ-620 — Cache the settings lookup on the request path

**Requirement:** The settings lookup runs once per request instead of once per widget.

**Acceptance Criteria:**
- One settings read per request, proven by a counted call assertion.

## Context — the run finished and produced ONE bundled durable lesson (INJECTED)

Review was clean and this run reached finalise. Asked for a durable lesson, the run recorded a **single
bundled entry** in `docs/LESSONS.md`:

> "The cache client's `get_or_set` helper silently swallows a serialisation error and returns the default,
> so a failed write looks like a cache miss forever. More generally, prove a guard can actually fail
> before trusting it — we trusted the helper's return value with no failing case. Also, in this codebase
> the settings table is the one place that is read on **every** request path, so its area is hotter than
> the row count suggests. And design's rule-compliance step could have checked the caching section of the
> rule book in this very run — the section exists and was never opened."

Run the learning loop on this entry. The unit of everything downstream is the **atomic claim**, not the
entry: split it first, then classify each claim (type + evidence + its recall handle) per the six types
and the two tiebreaks, and emit the counted `CLAIMS:` line. State how many claims the entry carries and
why each one is the type you propose, and say plainly whether your classification is a proposal or a
decision.

Do not stop for my input; show the artifacts you would produce.
