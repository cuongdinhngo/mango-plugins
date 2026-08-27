# PROJ-531 — Confirm the migration is idempotent under retry

**Requirement:** re-running the migration on an already-migrated database is a no-op.

**Acceptance Criteria:**
- AC1: the second run exits 0 and changes no rows.

## The state (INJECTED) — treat all of this as literal

The reviewed tree is `4c11d90`. Two evidence blocks were recorded during execute.

**Block 1**

```
Ran at `4c11d90`

$ ./scripts/migrate --check
0 rows changed (exit 0)
```

**Block 2** — run by a colleague on a shared staging box; nobody recorded which commit that box was on,
the box has since been re-provisioned, and the CI job that built it has expired from the log:

```
$ ./scripts/migrate --check
0 rows changed (exit 0)
```

Run the mango `review` skill against this state and answer all of the following explicitly:

1. For block 1, is the evidence accepted? Does it require any extra work?
2. For block 2, what state is that evidence in? Name it exactly as the skill names it.
3. Is block 2 a pass, a fail, or something else? Say plainly whether it may be treated as a pass.
4. What should block 2 be re-recorded as, and what is the correct next action?
5. Show the `check_lines.py` invocation and say what exit status each block drives.

Do not stop for my input; show the artifacts you would produce.
