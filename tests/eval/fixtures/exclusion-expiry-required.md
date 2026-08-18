# PROJ-410 — Layer assignment for the anchor repository index

**Requirement:** `assign_layers` groups every source file under a coherent architectural layer so the
sitemap renders one node per layer.

**Goal:** The layer assignment is sensible on the real anchor repository, not only on the fixtures.

**Acceptance Criteria:**
- AC1(a): `assign_layers` returns a layer for every indexed file (unit-testable on fixtures).
- AC1(b): the layer assignment is **sensible on the real anchor repository** — no single layer swallows
  the whole application. This can only be judged by running `assign_layers` over the real anchor index
  and a human eyeballing the result; there is no runner in this project that can assert "sensible".

## The design state (INJECTED) — treat all of this as literal

Assume Gate 1 cleared. The proposed proving test for **AC1(b)** is a **unit test over three synthetic
fixture files** — it does not touch the real anchor index. In the per-AC verification plan AC1(b) is
therefore classified **risk layer: runtime/manual**, **proof artifact: unit** → a layer-match
**mismatch**.

The design proposes to record AC1(b) as a coverage-gap exclusion in the working doc:

```
| Item   | Risk tier | Why deferred                         | Follow-up                                  |
| AC1(b) | high      | no runner can assert "sensible" here | the maintainer runs assign_layers on the anchor index and records the assessment |
```

Note: this exclusion record carries **no `expiry:` value**.

Run the mango `design` skill against this state and answer all of the following explicitly:

1. Does this exclusion, as written, count as a recorded coverage-gap exclusion? Why or why not?
2. What happens to the AC1(b) layer-match at Gate 2 — does the gate close or is it blocked?
3. What is the smallest change to the exclusion record that would make it count?
4. Emit the `EXCLUSIONS:` counted line for this working doc as it stands.

Do not stop for my input; show the artifacts you would produce.
