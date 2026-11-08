# How to set up a project for mango

> **In 30 seconds.** For whoever adds mango to a repo, once per repo. After these steps `.harness.json`
> exists, every value in it is confirmed, and `/mango:doctor` is green. Takes a short session.
> Needs: the prerequisites below and the plugin installed ([marketplace README](../../README.md)).

## Prerequisites

- **Claude Code** with plugin support.
- **git** — mango works on a branch and reviews the committed diff.
- **Python 3.7 or newer** on `PATH`. mango's checker scripts use only the standard library, so there is
  nothing to `pip install`. CI runs them on the current Python 3.
- **A test command** for your project (for example `npm test` or `pytest -q`).
- **A tracker connection, or local mode**: a CLI for tracker writes (`tracker.cli`) or a read-only
  MCP server for ticket reads (`tracker.read_mcp`). With no tracker, set
  `"tracker": { "mode": "local" }`: tickets are Markdown files in `tickets_dir`, mango makes no tracker
  call, and `finalise` prints the tracker update for you to apply. `/mango:doctor` reports ❌ with
  neither, and `/mango:solve` will not start while a ❌ remains.
- **Your PR host's CLI** (for example `gh`), named in `pr_host`, for `finalise` to open the PR.

## Steps

1. **Write `.harness.json`.** Run `/mango:init`: it detects the stack read-only, interviews you only for
   what it cannot detect, asks whether the file is committed or kept local, writes **no secrets**, and
   scaffolds a starter rule book if none exists. By hand instead: copy `config/harness.minimal.json` to
   `.harness.json`, replace each `REPLACE_ME`, create `tickets_dir`, and create the rule book file at
   `rulebook_path` — an empty file is enough to start. Every key: [config reference](../reference/config.md).
2. **Confirm every `UNVERIFIED` value.** `init` marks a guess as a guess; read each one back and confirm
   or correct it.
3. **Check the setup.**
   ```
   /mango:doctor
   ```
   You should see: `mango <version> @ <base path>` on the first line, then a ✅/⚠/❌ list.
4. **Give it rules (optional).** `init` gives you a skeleton rule book with TODOs; `/mango:codify` is the
   deeper facilitation for a project with no rule book, a thin one, or inconsistent conventions. It
   counts the patterns (presenting "pattern A: 12 files, B: 5" as **data**, not a verdict), asks you to
   pick each standard, and records the choices as provisional until you ratify them.
5. **Map the project (optional).** Two opt-in adapters generate regenerable, descriptive maps into
   `docs_dir`; the lifecycle runs fully without them. `/mango:sitemap` needs `code_map_cmd`;
   `/mango:db-map` needs `db_kind` plus `db_introspect_cmd` or `migrations_path`. A generated `db-map`
   lets `analysis` widen the blast radius to schema dependents; database *conventions* stay in the rule book.

## Check it worked

`/mango:doctor` shows no ❌. Then try `/mango:solve <KEY>` on a small ticket.

## If something goes wrong

| Symptom | Fix |
|---|---|
| Every skill stops and asks for `.harness.json` | Run step 1 in the project root. |
| `doctor` ❌ on `test_command` | It still reads `REPLACE_ME`; set your real test command. |
| `doctor` ❌ on the rule book | Create the file at `rulebook_path`; an empty file only warns. |
| `doctor` ❌ on the tracker | Set `tracker.cli`, or declare `"tracker": { "mode": "local" }` and create `tickets_dir`. |
| The version is not the one you installed | Read `doctor`'s first line; `/mango:version-check` (needs `update_check_url`) prints the update commands. |

## Next

- [The lifecycle](../concepts/lifecycle.md) — what each phase does and where it stops.
- [Unattended runs](../concepts/unattended-runs.md) — handing a ticket over for the night.
