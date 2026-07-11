---
name: budget
description: Facilitated, opt-in way to make mango's token cost visible and to adopt an external token optimizer with its safety trade-offs made explicit. Detects which optimizers are present, informs per a fixed safety axis (representation-redundancy only — never a check, gate, critic, or the evidence a critic relies on), and records a human's provisional adoption choice in .harness.json. It never installs an optimizer, never makes mango depend on one, and never silently changes what a critic emits.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md` — and especially its **descriptive vs normative /
observe-facilitate-never-author** boundary. `budget` is to token cost what `codify` is to the rule
book: it **measures and informs**, then lets a human choose. It **detects and informs, never
self-administers** — exactly like `codify` (never authors a rule) and `version-check` (never installs
a plugin). This skill exists because field cost was always an **estimate**, never measured per-phase
(`context ≠ correctness`, applied to optimization: **don't optimize what you haven't measured**).

> **The boundary (binding).** `budget` may **detect** which optimizers exist and **report** measured
> cost (the Cost ledger). It may **facilitate** adopting an optimizer by **stating its safety
> trade-offs and asking the human to choose**. It must **NEVER** install an optimizer, **never** make
> mango *depend* on one, **never** let one weaken a check / gate / critic, and **never** silently
> change what a critic emits. Every adoption is a **recorded decision — PROVISIONAL until a human
> ratifies it** (like `codify`), never a silent toggle. Detect-and-inform, never self-administer.

`budget` is **opt-in and read-only on the system**. It writes only the `token_optimizer` block in
`.harness.json` (the recorded human choice) and reads/reports the Cost ledger. It is **not** part of
the lifecycle.

## The safety axis (governs every choice here)

A token optimizer is **safe** only if it removes **representation redundancy** — *how* output is
phrased — and **never** removes a check, a gate, a critic, or the **evidence detail** a critic relies
on (`path:line`, measured values, per-clause verdicts, diffs). Judge every optimizer against that one
axis:

- **RTK** — compresses **Bash-command output** (git / test / lint / ls) *before* it enters context.
  **Safe:** tests still run fully; only noise is trimmed; no decision, gate, or critic is touched.
  Sits **below** mango. This is the default-expect optimizer (see below).
- **Headroom (input compression)** — compresses tool output / files / logs and is **reversible**
  (originals retrievable). The compression itself is **safe**. **BUT** its `OUTPUT_SHAPER` /
  effort-routing changes what the model *writes* and *how hard it thinks* → it can weaken a critic →
  it **must stay OFF** for mango (`headroom.output_shaper: false`, enforced).
- **Caveman** — compresses what the agent **says** (terse output). This optimizes exactly what mango
  **deliberately refuses** for critics: a one-line review loses the `path:line` evidence that *is* the
  review's value. **Caveman-style compression must never touch critic output** (reviewer, challenger,
  any gate-blocking artifact); if enabled at all it is **scoped to non-critic output only**
  (`caveman.scope: "non-critic-only"`, enforced — see the guardrail below).

## Steps

1. **Detect (read-only, facts only).** Report which optimizers are present on the system — the RTK
   binary / hook, a Headroom install, a Caveman skill — as **facts**. Run detection via the Bash tool
   (e.g. `command -v`), or note "cannot detect from here". **Install nothing.** State plainly what is
   present and what is absent; absence is not a problem to fix.
2. **Inform per the safety axis.** For **each** detected optimizer, state plainly what it compresses
   and classify it **safe** / **output-shaping (must stay off)** / **critic-risky (non-critic-only)**
   per the axis above. Do not recommend a default; present the trade-off and let the human weigh it.
3. **Human-gate adoption (recorded, provisional).** Record the human's choice in
   `${CLAUDE_PROJECT_DIR}/.harness.json` under `token_optimizer`, e.g.:

   `{ "rtk": "expect", "headroom": { "enabled": false, "output_shaper": false }, "caveman": { "enabled": false, "scope": "non-critic-only" } }`

   Two invariants are **hard-pinned and non-negotiable**, so the human may only choose *within* them:
   `headroom.output_shaper` stays **false** and `caveman.scope` stays **"non-critic-only"**. Adoption
   is a **recorded decision, PROVISIONAL until ratified** — never a silent toggle. mango **never
   installs** the optimizer and never comes to **depend** on it: with the block set to any value, the
   lifecycle runs identically (see RTK degrade-clean below).
4. **Report the effect in the Cost ledger (measure the optimizer, don't trust its claim).** For each
   enabled optimizer, record in the working-doc **Cost ledger** what it is estimated/measured to save,
   so its effect is itself a counted, visible fact — not a vendor claim taken on faith. The ledger
   stays **descriptive**: it reports cost and savings; it never itself decides to cut anything.
5. **Boundary self-check.** Confirm before finishing: nothing was installed; mango depends on no
   optimizer (RTK absent → identical behaviour); no critic output was compressed
   (`caveman.scope: non-critic-only` holds and critic output keeps `path:line` + measured values);
   `headroom.output_shaper` is false; every recorded adoption is PROVISIONAL until the human ratifies.

## RTK — default-expect, below mango, degrade cleanly

The default `.harness.json` sets `token_optimizer.rtk: "expect"`: mango **assumes RTK may rewrite
Bash-command output** (git / test / lint / ls) into a compact form and **tolerates it**. mango does
**not** install RTK and does **not** require it.

- **Degrade cleanly.** If RTK is **absent**, everything works **identically** — only the saving is
  lost. mango must **never fail, block, or change a decision** based on RTK presence/absence. No mango
  logic may parse an RTK-specific output format in a way that breaks without RTK.
- `doctor` may print RTK presence as one **informational** line — never a ✅/⚠/❌ that gates anything.

## Caveman critic guardrail (HARD — invariant)

**Caveman-style output compression must never be applied to critic output** — the `reviewer`, the
`challenger`, and any gate-blocking artifact. Critic output **must retain full evidence detail**:
`path:line`, measured values, per-clause verdicts, corrected snippets. A terse one-line review loses
the evidence that *is* the review's value — and brevity applied where a **false-green could hide** is
exactly the retro-#5 failure class. Caveman, if enabled at all, is **scoped to non-critic output
only** (conversational replies, commit messages); `.harness.json` records `caveman.scope:
"non-critic-only"` and mango enforces it. The reviewer / challenger agent briefs carry the same
guardrail.
