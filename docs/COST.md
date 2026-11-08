# Cost — measured on real tickets

**No measurements are recorded yet.** This page holds the protocol and an empty table. Every row
added must come from a real ticket run, printed by `ticket_stats.py`, and read by a human before it
is added. Until a lane has at least three rows, it has no median and this page states no cost for it.

## The table

| Lane | Scope (S/M/L / files) | Dispatches | Dispatch tokens | Unmeasured | Session tokens | Minutes | Gates cleared | Not met (real/raised) | mango | Date |
|---|---|---|---|---|---|---|---|---|---|---|

**Median per lane:** none yet — a median needs three or more rows in that lane.

## Making a row

Run the script in the project, on the ticket's working doc. It reads the doc and writes nothing:

```
python3 <mango>/scripts/ticket_stats.py <workdoc> --row [--session-tokens <n>] [--minutes <n>]
        [--real <n>] [--mango <x.y.z>] [--lane quick|full|autorun]
```

Every cell has a fixed shape — a number, a fixed word, a version or a date — so no ticket key, path,
name or text from the doc can reach the row. `validate.py` refuses a row here with any other column or
any cell outside its shape. Without `--row` the script prints the same fields as one line:
`COST: lane=… scope=… … date=…`. Exit 3 means a field the doc should carry was not found and is
printed `unknown`.

## What each column measures

- **Lane** — `quick` for `TIER: lite`; `autorun` when a `DISCLOSURE` list sits under the doc's
  `## Phase 5`; otherwise `full`. `--lane` corrects it for a doc written before 1.21.1.
- **Scope** — the doc's `SCOPE` letter, then the number of files on its `Reviewed at` line.
- **Dispatches, Dispatch tokens, Unmeasured** — the rows of the doc's **Cost ledger**, the sum of
  their Tokens cells, and the count of `unmeasured` cells. The ledger is **dispatch-only**: one row per
  subagent return. An unmeasured cell is counted, never filled in.
- **Session tokens** — the host's own usage figure for the whole session, which includes the main
  loop. mango does not measure the main loop, and it is the larger term. It is not in the doc: pass
  `--session-tokens`, or it stays `unknown` — never estimated from the dispatch total.
- **Minutes** — from the first command to the last gate (or the PR, for `autorun`). Not in the doc:
  pass `--minutes`, or it stays `unknown`.
- **Gates cleared** — the doc's `Gate <n> status:` lines that read `cleared`. In `autorun` they were
  closed on artifacts, not by a human.
- **Not met (real/raised)** — raised is the `not met` count on the first `CHALLENGER VERDICT` line;
  real is how many of those were real defects, a human judgement passed as `--real`. `n/a` on the
  quick lane, which runs no challenger.
- **mango** — the version that ran the ticket (`--mango`, from `doctor`'s first line).
- **Date** — the doc's `Last updated:` date.

## Protocol

External users can report a run with the **Field report** issue template; it asks for this row.

1. Run **three or more real tickets per lane**, chosen as you would for work, not to flatter a lane.
2. At the end of each ticket, run `ticket_stats.py --row` on its working doc, with the host's session
   figure and the minutes if you have them.
3. Read the row before it leaves the project. The ticket's text, each `not met` item and the doc
   itself stay there.
4. Add one row per ticket. Compute a lane's median only once it has three rows.
5. Once each lane has three rows, add two or three sentences below on when the cost is worth paying.

## When this cost is worth it

Not written yet. It will be written from the rows above, not before them.
