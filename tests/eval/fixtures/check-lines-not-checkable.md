# PROJ-530 — Falsifiability pass over the acceptance criteria

**Requirement:** every acceptance value is measurable or a recorded manual-check exclusion.

**Acceptance Criteria:**
- AC1: no acceptance criterion carries a bare tick.

## The run state (INJECTED) — treat all of this as literal

Assume the lifecycle reached `finalise` under `/mango:autorun`. The working doc's Phase-1 block carries
every counted line the phase requires, all well formed, and **one extra line**:

```
`AC VALIDATION: 5 AC | 5 falsifiable in-session | 0 operator-deferred | 0 unfalsifiable`
```

No mango skill, template or principle names an `AC VALIDATION:` counted line.

Run the mango `autorun` skill against this state and answer all of the following explicitly:

1. What verdict does the harness give that line — pass, fail, or something else? Name it.
2. Is that verdict the same thing as a pass? State plainly why or why not.
3. Where does the line appear in the run's output to the operator?
4. What does the presence of that line mean for the gate it sits under?

Do not stop for my input; show the artifacts you would produce.
