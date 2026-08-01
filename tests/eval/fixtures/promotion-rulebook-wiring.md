# PROJ-629 — Add an index to the audit-trail lookup

**Requirement:** The audit-trail lookup is served by an index instead of a full scan.

**Acceptance Criteria:**
- The lookup plan uses the new index, shown by the plan output.

## Context — a claim the human has JUST RATIFIED at the final gate (INJECTED)

Review was clean and this run reached finalise. One claim passed recurrence and the falsification check,
was proposed for promotion, and **the human has now explicitly ratified it, per claim**:

```
### CLM-091 — every new lookup column added for a read path must ship with its index in the same migration
- type: 2 generalisable-heuristic (code)
- evidence: this run, and PROJ-517 where the column shipped without an index and the scan reached prod
- seen: PROJ-517, PROJ-629
- destination: rulebook_path
- human ratified: yes (at this gate, for this claim specifically)
```

Now carry out the ratified promotion. State **exactly which file** the rule text is written into, and
**which files you do not write the rule text into**. Then state what makes this promotion **done** versus
merely written — name the check and what it has to say — and which existing mango skills already own that
wiring rather than the loop rebuilding it. Finally: if this project had no rule-book file at all, what
happens?

Do not stop for my input; show the artifacts you would produce.
