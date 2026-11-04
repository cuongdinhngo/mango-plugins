# Adopting mango in a team

A four-week rollout. Each week has **one action** and **one number** to record, so the decision to go
further is made on what you measured, not on this page.

## Week 1 — observe, commit to nothing

**Action:** run `/mango:challenge <ticket-file> <base>..<branch>` on 5–10 pull requests your team
merged recently. It needs no `.harness.json` and writes nothing.

**Measure:** the `not met` items it raised, and how many of them were real defects (`real / raised`).
This is the number to show the team. A high `raised` with a low `real` is also a finding.

## Week 2 — the light lane

**Action:** copy `config/harness.minimal.json` to `.harness.json` (local mode needs no tracker),
create `tickets_dir` and the rule book file at `rulebook_path`, and run `/mango:doctor` until it
shows no ❌. Use `/mango:quick <KEY>` for single-file bug fixes.

**Measure:** tickets run through `quick`, and how many a reviewer finding sent back before merge.

## Week 3 — the full lifecycle on risky tickets

**Action:** run `/mango:solve <KEY>` on tickets sized M–L, or touching the globs you list in
`high_stakes_paths`. Connect a tracker (`tracker.cli`, `tracker.read_mcp`) if you want one.

**Measure:** per ticket, the challenger's `not met` items that were real, and the cost — record both
in the shape of [`COST.md`](./COST.md).

## Week 4 — the rule book

**Action:** run `/mango:codify`. It counts the conventions your code already uses and asks you to
choose each standard; ratify the ones you keep. Between tickets, run `/mango:promote` once a lesson in
`lessons_path` has recurred on two or more tickets.

**Measure:** rules ratified, and rules still provisional.

## When not to use mango

- Prototypes and spikes, where the code is expected to be thrown away.
- Tickets with no acceptance criteria — the matrix and the challenger have nothing to check against.
- Changes where the gates cost more attention than the change carries risk; use `quick`, or nothing.

## FAQ

- **What does it cost?** See [`COST.md`](./COST.md). It holds measured rows only; until a lane has
  three, it states no figure.
- **Where does our data go?** mango's scripts are standard-library only and open no connection of their
  own; under `autorun`, `RECONCILE` runs the read-only checks its run contract names, such as the PR
  host's view command. Outward actions are the PR host CLI (`pr_host`) and `tracker.cli`, each behind
  its own approval in `finalise`; `tracker.read_mcp` reads tickets; `/mango:version-check` fetches
  `update_check_url` only when you set it. Model traffic is your Claude Code session's own.
- **Does it run on other hosts?** See [`MATURITY.md`](./MATURITY.md).
- **How do we stay on one version?** Pin the marketplace to a release tag — see *Update and pin* in
  the [root README](../README.md#update-and-pin).
