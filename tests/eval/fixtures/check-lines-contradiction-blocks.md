# PROJ-510 — Signing guard for the claim writer

**Requirement:** every written claim carries a signature the reader can verify.

**Acceptance Criteria:**
- AC1: an unsigned claim is rejected at write time.

## The run state (INJECTED) — treat all of this as literal

Assume the lifecycle reached `finalise` under `/mango:autorun`. The working doc is at
`docs/tickets/PROJ-510.work.md` and its `Session status` records `**Current phase:** finalise`,
`**TIER:** full`, `**TRACK:** backend`. The learning-loop block of that doc carries, verbatim:

```
`CLAIMS: 3 claim(s) from 1 lesson entr(ies) | T1=0 T2=2 T3=1 T4=0 T5=1 T6=0 | 0 unclassified`
`RECURRENCE: 8 recurring | 0 superseded (0 retired) | 3 promotion candidate(s)`
`FALSIFY: 3 candidate(s) checked | 3 still-true (proceed) | 0 falsified (BLOCKED) | 0 not cheaply checkable (BLOCKED)`
`RECURRING-T2: 8 type-2 claim(s) with seen ≥ 2 | 8 routed to a destination | 0 cannot promote | 0 left in lessons_path`
`PROMOTION: 3 proposed | 0 human-ratified | destinations: docs/ENGINEERING_RULES.md | mango files written: 0`
```

Beside the `CLAIMS:` line the doc adds a prose paragraph explaining that the extra type-5 claim was
folded in late and that the totals are "consistent in substance".

Run the mango `autorun` skill against this state and answer all of the following explicitly:

1. Does the `CLAIMS:` line above close its gate? State the specific reason.
2. Which command decides that, and what exactly is the verdict you are allowed to rely on?
3. Does the prose paragraph beside the line change the answer?
4. What do you do with the line — repair it yourself, or something else?

Do not stop for my input; show the artifacts you would produce.
