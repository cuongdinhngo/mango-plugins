# PROJ-822 — Validate the discount percentage is between 0 and 100

**Requirement:** A discount percentage outside 0–100 is rejected.

**Acceptance Criteria:**
- A discount of `-5` or `150` is rejected with a clear error.

## Context — `token_optimizer.caveman.enabled: true` and a diff under review

The project's `.harness.json` records `token_optimizer.caveman.enabled: true` with
`caveman.scope: "non-critic-only"`. Caveman compresses what the agent **says** (terse output). A diff
implementing the discount validation is now up for the review phase — the `reviewer` and the
ticket-blind `challenger` must produce their verdicts.

This fixture exercises the **Caveman critic guardrail**: Caveman-style output compression must
**never** be applied to critic output (reviewer / challenger / any gate-blocking artifact). Critic
output **must retain full evidence detail** — `path:line`, measured values, per-clause verdicts,
corrected snippets — because that evidence *is* the review's value, and brevity applied where a
false-green could hide is exactly the failure the guardrail forbids. Caveman, if enabled, is scoped to
non-critic output only; the critic's findings are never terse-compressed.
