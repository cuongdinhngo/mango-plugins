# PROJ-550 — Add a trailing-slash redirect to the health endpoint

**Requirement:** `GET /health/` redirects to `GET /health` with a 308.

**Acceptance Criteria:**
- AC1: `GET /health/` returns 308 with `Location: /health`.

## The state (INJECTED) — treat all of this as literal

This is a **brand-new project's first ticket**. `/mango:init` has just run. There is no
`config.lessons_path` file, no `config.drift_path`, no rule book beyond `init`'s template of `TODO`s,
and no prior ticket. `config.track` is `backend`. The ticket is clear: nothing to expose.

The working doc at `docs/tickets/PROJ-550.work.md` records `**Current phase:** finalise`,
`**TIER:** full`, `**TRACK:** backend`, and carries every counted line the lifecycle requires, each one
in the canonical grammar with **every count at zero** — no claims, no handles, no exclusions, no
promotions, one dispatch in the ledger.

Run the mango `autorun` skill against this state and answer all of the following explicitly:

1. Run the counted-line check. What is the verdict?
2. Does an all-zero line count as emitted, or as missing?
3. Does the check add any step, warning, question, or block to this first ticket? Answer plainly.
4. List anything the operator has to do that they would not have had to do before this check existed.

Do not stop for my input; show the artifacts you would produce.
