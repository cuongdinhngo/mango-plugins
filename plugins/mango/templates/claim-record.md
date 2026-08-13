# Claim record — the one shape the learning loop writes and reads

The learning loop's unit is the **atomic claim**, not the lesson entry. `finalise` writes claims in this
shape; `refine`/`analysis` recall reads the same shape. One shape, one place — a writer and a reader
that disagree on the fields make recall silently miss.

Append each claim under `config.lessons_path` (type 1 lives there permanently; every other type keeps
its claim record there and names the destination it was promoted to, so provenance survives the move).

```
### <CLAIM-ID> — <the claim, one falsifiable sentence>
- type: <1 tool-constraint | 2 heuristic | 3 skill-gap-signal | 4 world-fact | 5 project-ground-truth | 6 adjudicated-non-defect>
- status: proposed (awaiting human confirm) | confirmed
- evidence: <path:line | the command + its output | the finding that proved it>
- handle: symbol:<import / API>        # type 1 — the RECALL KEY. A symbol, not a slug.
- handle: <class-slug>                 # type 2 — the RECALL KEY. A short kebab-case slug naming the
                                       #   CLASS of heuristic (e.g. `blast-radius-grep`), never a
                                       #   symbol and never an area: a heuristic holds across tools.
- area: <domain / area>                # type 5 — the RECALL KEY. An area, NOT a symbol.
- sub-shape: descriptive | normative | environment   # type 5 only
- re-raise: <the finding this pre-empts>             # type 6 — the RECALL KEY
- expiry: <the condition that ends this acceptance>  # type 6 — MANDATORY
- verified-at: <YYYY-MM-DD | commit sha>             # type 5-environment — MANDATORY (it rots)
- destination: <the PROJECT path this claim's promotion targets, or "stays in lessons_path">
- seen: <KEY>, <KEY>, …                # the recurrence ledger — one ticket key per sighting
- supersedes: <CLAIM-ID>               # this claim NARROWS or FALSIFIES that one
- retired: <reason> — superseded by <CLAIM-ID> | human-retired
  # recall SKIPS a retired claim; the record STAYS (history is never deleted, and there is no auto-retire)
```

## Field rules

- **`status:` is `proposed` until a human confirms the type.** The classifier proposes; it never
  classifies-and-acts.
- **The recall key is per type.** Type 1 is recalled by **symbol**, **type 2 by its class `handle:`**,
  type 5 by **area**, type 6 by **the
  finding that would otherwise be re-raised**. A type-5 claim given a symbol handle instead of an area
  will not surface when it should.
- **A type-2 claim MUST carry a `handle:`.** A heuristic holds across tools, so neither a symbol nor an
  area can key it; without a class slug it is unrecallable and cannot reach the next ticket. A type-2
  claim with no `handle:` is a finding at classification.
- **`expiry:` on every type 6, `verified-at:` on every type-5-environment claim.** A type-6 entry with
  no expiry is a permanent exemption nobody chose; an environment fact with no stamp is indistinguishable
  from a current one.
- **`seen:` is a list, not a counter.** Recurrence is *which tickets*, so a claim's history is auditable
  rather than a number that cannot be checked.
- **Supersession replaces, it does not delete.** A claim that narrows or falsifies an earlier one
  records `supersedes:`, and the earlier one gets `retired: … superseded by <CLAIM-ID>`.
- **Every destination is a path in the PROJECT repo.** No claim's destination is ever a mango file.
