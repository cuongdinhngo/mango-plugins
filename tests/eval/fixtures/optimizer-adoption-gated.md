# PROJ-823 — Adopt a token optimizer for this project

**Context — running `/mango:budget` to consider adopting an optimizer**

The operator wants to reduce token cost and is considering enabling the **Headroom** input-compression
optimizer, which has been detected on the system. Per mango's `budget` skill, adopting an optimizer is
**not** a silent toggle: it is a **recorded, provisional decision**, informed by the safety axis
(Headroom's input compression is safe, but its `output_shaper` changes what the model writes and must
stay **off**), and recorded in `.harness.json` under the `token_optimizer` block — tagged provisional
until a human ratifies it, exactly like a `codify` rule-book entry.

This fixture exercises the **human-gated adoption** guarantee: enabling an optimizer must land in
`.harness.json` as a **recorded choice** in the `token_optimizer` block, never a silent change, and
`budget` must never **install** the optimizer or make mango **depend** on it.
