## Token cost — measure before you optimize (descriptive ledger + human-gated optimizers)

> **mango measures its own token cost as a counted, descriptive artifact, and adopts a token
> optimizer only through a human gate with the safety trade-offs made explicit — it never installs
> one, never depends on one, and never lets one weaken a check, a gate, a critic, or the evidence a
> critic emits.**

- **The Cost ledger is descriptive.** The run records token usage **per subagent dispatch** (reviewer,
  challenger, extractor, Explore fan-out, each review round) into the working doc as a **facts-only**
  counted artifact — **one row emitted per dispatch return as a mechanical by-product of dispatching**
  (N dispatches → N rows), not bookkeeping the model is asked to remember; `finalise` surfaces a
  one-line summary (total + top cost driver). It **never** auto-cuts anything — it makes cost **visible**
  so a *human* can decide. Cost was always an **estimate**, never measured per-phase; `context ≠
  correctness` applied to optimization means **don't optimize what you haven't measured** — the ledger
  is that measurement, and the data a later middle-tier sizing decision needs. The ledger is
  **dispatch-scoped**: it measures subagent dispatch only — main-loop output noise is **not measured by
  mango**, so it implies no dispatch-vs-noise split; the optimizer reports its **own** savings (`rtk
  gain`) for that domain. **Ledger completeness is gate-checked at finalise** (the ledger's teeth):
  the ledger is complete only when **every dispatch row is present AND its token cell carries a value** —
  a real count or the explicit `unmeasured (blocking retrieval)` marker; a missing row **or** a blank
  token cell is incomplete and blocks like an unfilled matrix column. It checks the **presence** of a
  value or an honest marker — it never inspects, ranks, judges, invents, or auto-cuts a value — so the
  ledger stays descriptive.
- **Emit deltas into the response, not full artifacts.** The working doc on disk is the **single source
  of truth** and is written **complete on disk**; the conversation gets only the **delta** on a partial
  update — the changed row/cell, "ledger **unchanged except** row N" — never a full reprint of the
  ledger / matrix / proof-manifest / working doc each time. This is a **representation-redundancy** cut
  on the safety axis (below): it changes only *how much of an unchanged artifact is re-pasted into the
  response*, never a check, a gate, a critic, or the artifact **written to disk**. The content-
  completeness gate still reads the artifact complete on disk — emit-less-into-the-response is not
  store-less-on-disk, and a delta references the rest, it never deletes it.
- **The safety axis (governs every optimizer choice).** An optimizer is **safe** only if it removes
  **representation redundancy** — *how* output is phrased — and **never** a check, a gate, a critic,
  or the **evidence detail** a critic relies on (`path:line`, measured values, per-clause verdicts,
  diffs). **RTK** (compresses Bash-command output before it enters context) is safe and sits **below**
  mango. **Headroom** input compression is safe, but its `OUTPUT_SHAPER` / effort-routing changes what
  the model writes and how hard it thinks → it **must stay OFF** for mango. **Caveman** (terse agent
  output) optimizes exactly what mango refuses for critics.
- **RTK default-expect + degrade cleanly.** The default `token_optimizer.rtk: "expect"` means mango
  **tolerates** RTK rewriting Bash output into a compact form; it does **not** install RTK and does
  **not** require it. If RTK is absent, everything runs **identically** — only the saving is lost.
  mango must never fail, block, or change a decision on RTK presence/absence, and no mango logic may
  parse an RTK-specific format in a way that breaks without RTK.
- **Caveman critic guardrail (HARD — invariant).** Caveman-style output compression **must never** be
  applied to critic output — the `reviewer`, the `challenger`, and any gate-blocking artifact — which
  **must retain full evidence detail** (`path:line`, measured values, per-clause verdicts). Terse
  critic output loses the evidence that **is** the review's value; **brevity is never applied where a
  false-green could hide** — the retro-#5 class, where a self-reported ✅ stood in for an unproven
  thing. Caveman, if enabled, is **scoped to non-critic output only** (`caveman.scope:
  "non-critic-only"`) and mango enforces it.

Adoption of any optimizer is a **recorded, PROVISIONAL decision** (via `/mango:budget`, ratified like
`codify`), never a silent toggle. Enforced at `budget` (detect + inform + the recorded human choice),
the `reviewer`/`reviewer-max`/`challenger` briefs (the critic guardrail), and `scripts/validate.py`
(the `budget` contract, the `token_optimizer` schema, and the critic-guardrail token).
