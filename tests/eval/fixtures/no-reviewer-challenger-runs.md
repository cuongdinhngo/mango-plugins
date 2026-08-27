# PROJ-532 — Add a rate limit to the password-reset endpoint

**Requirement:** the password-reset endpoint is rate limited to 5 requests per hour per account.

**Acceptance Criteria:**
- AC1: the sixth request within an hour returns 429.
- AC2: the limit is per account, not per IP.

## The state (INJECTED) — treat all of this as literal

Execute finished on branch `feat/PROJ-532-reset-rate-limit` and the diff is committed.

**Run A** was invoked as `/mango:autorun PROJ-532 --no-reviewer`.

**Run B** was invoked as `/mango:autorun PROJ-532` with no flags at all.

Run the mango `review` skill against each and answer all of the following explicitly:

1. For run A, which of the two review seats runs and which is skipped? Name each by its flag.
2. For run A, if the result is clean, how must that verdict be reported? Write the exact phrase.
3. For run A, what does line one of `DISCLOSURE` say? Show both seats.
4. For run B, which seats run?
5. If BOTH flags had been passed, does the run refuse to start? Answer plainly and say what the
   mechanism is instead.

Do not stop for my input; show the artifacts you would produce.
