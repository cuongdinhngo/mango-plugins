# PROJ-520 — Group indexed files into architectural layers

**Requirement:** `assign_layers` buckets every indexed source file into an architectural layer so the
overview renders one node per layer.

**Acceptance Criteria:**
- AC1: `assign_layers` returns a layer string for every indexed file (no file left unassigned).
- AC2: the layers it produces are **sensible** — no single layer swallows the whole application, and
  dependency directories do not dominate the result.

## The design state (INJECTED) — treat all of this as literal

Assume Gate 1 cleared. `.harness.json` sets `real_corpus_path` to a real indexed repository that exists
on disk. The proposed per-AC verification plan reads:

```
| AC  | risk layer | proof artifact | fixture provenance | layer-match? |
| AC1 | logic      | unit           | n/a                | ✅           |
| AC2 | logic      | unit           | authored           | ✅           |
```

AC2's unit test builds **four synthetic fixture files** the change itself authored, and asserts the
grouping over them. Nothing in the run touches the configured corpus.

**Variant B — same plan, plus this coverage-gap exclusion record for AC2:**

```
| Item | Risk tier | Why deferred                  | Follow-up                        |
| AC2  | high      | no runner can assert sensible | the maintainer eyeballs the result |
```

This record carries **no `expiry:` value**.

Run the mango `design` skill against this state and answer all of the following explicitly:

1. Is AC2 an input-shape-dependent AC? Say why, using the trigger the skill defines.
2. Is `authored` an acceptable fixture provenance for AC2? What is AC2's layer-match, and does Gate 2
   close or is it blocked?
3. For variant B, does the exclusion make AC2 pass? Why or why not?
4. Emit the `EXCLUSIONS:` counted line for the plan as it stands (variant A).

Do not stop for my input; show the artifacts you would produce.
