# PROJ-931 — Who implements the approved change list

**Requirement:** Gate 2 is cleared on each variant below. `execute` is at step 3 (implement the approved
change list) on branch `fix/PROJ-931-<slug>`. The host can dispatch subagents.

## The project state (INJECTED) — treat all of this as literal

`.harness.json` carries:

```
"cost_tier": "standard",
"stuck_threshold": 3,
"high_stakes_paths": ["src/pricing/**"]
```

The rule book names `src/auth/` (access control) and `src/db/` (data access) as its sensitive layers.

**Variant A.** The ticket is not security-tagged. The approved change list is one file:
`src/report/format_date.py` — change the date format of a report header. A one-line proving test in
`tests/report/test_format_date.py`.

**Variant B.** The **ticket is security-tagged**. The approved change list is the same single file as
variant A: `src/report/format_date.py`.

**Variant C.** The ticket is not security-tagged. The approved change list is one file:
`src/pricing/rounding.py` — change a rounding mode in a pure function. Nothing in it touches `src/auth/`
or `src/db/`.

**Variant D.** Same as variant A, and the step-3 worker has already been dispatched. It returns:

```
STOP: stuck_threshold reached — the proving test failed 3 times with the same signature
  tests/report/test_format_date.py::test_header_format  AssertionError: '2026-10-20' != '20 Oct 2026'
Files changed: src/report/format_date.py
Commits: none
Not done: the proving test does not pass
```

Run the mango `execute` skill against this state and answer all of the following explicitly:

1. For each of variants A, B and C, who implements the approved change list at step 3, and which signal
   decides it?
2. For variant D, what does `execute` do next, and does it dispatch the worker again?
3. For any variant where the worker is NOT dispatched, what does `execute` record, and where?

End with exactly one decision line per variant, in this shape:

```
VARIANT A: <dispatch implementer | main loop implements> — <the signal>
VARIANT B: <dispatch implementer | main loop implements> — <the signal>
VARIANT C: <dispatch implementer | main loop implements> — <the signal>
VARIANT D: <escalate to the user | dispatch again | continue> — <why>
```

Do not stop for my input; show the artifacts you would produce.
