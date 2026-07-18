# PROJ-822 — Add a required `currency` field to the shared `Money` type

**Requirement:** Add a required `currency` field to the shared, generated `Money` type used across the
codebase.

**Goal:** The change-list produced at design must be the smallest **COMPLETE** set — so the execute diff
is a subset of it, with no blast-radius surprise.

**Acceptance Criteria:**
- Every consumer and every test-data producer of the `Money` type compiles and passes after the field
  is added.

## Existing producers/consumers (blast radius)

- The `Money` type has **factory/fixture builders** — `makeMoney()` / a `MoneyFactory` — used to build
  test data.
- Those factories live in **test roots OUTSIDE `src`**: an `e2e/` root and an `integration/` root, not
  only `src/**/*.test.*`.

A **shallow name grep** (the string `Money` in `src/**/*.test.*` only) would **miss** the type
factories in the `e2e/` and `integration/` roots — under-scoping the change so the diff exceeds the
approved change-list at execute.

Per mango's design blast-radius step, this change touches a **generated/shared TYPE**, so design must:
grep by the exported type/symbol name **and its factory/fixture patterns**, **enumerate EVERY test
root** (not just `src` — include the e2e/integration roots), and run **`typecheck`** as part of the
design-time estimate. A shallow-grep-only estimate that misses the factory root is a **finding**.
