# Cost — measured on real tickets

**No measurements are recorded yet.** This page holds the protocol and an empty table. Every row
added must come from a real ticket run, anonymised, with its mango version, model and date. Until a
lane has at least three rows, it has no median and this page states no cost for it.

## The table

| Lane | Ticket (S/M/L, files touched) | Dispatch tokens | Session tokens | USD | Wall-clock | Gates approved | Challenger `not met` caught | `cost_tier` | mango / model / date |
|---|---|---|---|---|---|---|---|---|---|

**Median per lane:** none yet — a median needs three or more rows in that lane.

## What each column measures

- **Lane** — `quick`, full (`/mango:solve`), or `autorun`.
- **Dispatch tokens** — the sum of the **Cost ledger** in that ticket's working doc (the
  `## Cost ledger` section of `templates/ticket.md`). The ledger is **dispatch-only**: one row per
  subagent return (reviewer, challenger, implementer, explorer, extractor). Report the count of
  `unmeasured (blocking retrieval)` cells beside the sum; never fill one in.
- **Session tokens** — the host's own usage figure for the whole session, which includes the main
  loop. mango does not measure the main loop, and it is the larger term. If the host shows no
  figure, write `unknown` — never estimate it from the dispatch total.
- **USD** — session tokens priced at the model's published rate **on the date of the run**; name the
  rate used. `unknown` session tokens → `unknown` USD.
- **Wall-clock** — from the first command to the last gate (or the PR, for `autorun`).
- **Gates approved** — the gates a human closed, including any sent back and re-closed.
- **Challenger `not met` caught** — `not met` items the challenger raised that were real defects,
  as `real / raised`. This is field evidence of what the independent check finds.
- **`cost_tier`** — the `cost_tier` value in `.harness.json` for the run.

## Protocol

External users can report a run with the **Field report** issue template; its fields are these columns.

1. Run **three or more real tickets per lane**, chosen as you would for work, not to flatter a lane.
2. At the end of each ticket, copy the working doc's Cost ledger total and the host's session figure.
3. Anonymise: project names, paths, ticket keys and customer names become placeholders (`PROJ-123`,
   `src/<module>/…`); keep the structure and every number.
4. Add one row per ticket. Compute a lane's median only once it has three rows.
5. Once each lane has three rows, add two or three sentences below on when the cost is worth paying.

## When this cost is worth it

Not written yet. It will be written from the rows above, not before them.

## Proposed: a one-line cost summary (not implemented)

No mango skill prints a copyable per-ticket cost line today; the figures above are read off the
working doc. A format for the maintainer to accept or reject — **nothing emits it yet**:

```
COST: lane=<quick|full|autorun> scope=<S|M|L>/<files> dispatch_tokens=<n> unmeasured=<k> session_tokens=<n|unknown> wall=<minutes> gates=<n> not_met=<real>/<raised> cost_tier=<tier> mango=<version> model=<id> date=<YYYY-MM-DD>
```
