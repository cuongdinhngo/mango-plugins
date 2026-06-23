---
name: db-map
description: Opt-in, descriptive map of the database schema — tables, columns + types, primary/foreign keys, indexes, relationships, and views/procedures — written into config.docs_dir. Generates regenerable facts, never normative rules. OFF by default; needs config.db_kind plus either config.db_introspect_cmd or config.migrations_path. Not part of the lifecycle.
---

Operate under `${CLAUDE_PLUGIN_ROOT}/PRINCIPLES.md`. This skill is **descriptive only**: it generates
**facts** about the schema (regenerable, falsifiable). The database is where the costliest mistakes
live and where the reviewer/challenger are blindest — but a schema map is the most stack-specific
thing of all, so it is opt-in and never core. The **normative** "database conventions" (naming,
timestamps, soft-delete, FK policy, migration style) live in the `codify` rule book, **not here**.

`db-map` is **OFF by default** — it needs database access or migration files — and the lifecycle runs
fully whether or not it has ever been generated.

## Steps

1. **Check configuration.** Read `${CLAUDE_PROJECT_DIR}/.harness.json`. The map needs `config.db_kind`
   plus **either** `config.db_introspect_cmd` (a project-supplied read-only introspection command)
   **or** `config.migrations_path` (a directory of migration files to derive the schema from). If the
   required config is absent, **report that `db-map` is not configured** (name `config.db_kind`,
   `config.db_introspect_cmd`, `config.migrations_path`, `config.docs_dir`) and **do nothing else**.
2. **Generate the schema map (read-only).** Run `config.db_introspect_cmd` if set, else parse the
   files under `config.migrations_path`, to produce: **tables**, **columns + types**, **primary /
   foreign keys**, **indexes**, **relationships**, and **views / stored procedures** if present.
   Introspection must be **read-only** — never alter, migrate, or write the schema. Delegate bulk
   read-and-extract to the Haiku `extractor` per `PRINCIPLES.md`.
3. **Write it to `config.docs_dir`.** Write a regenerable map file under `config.docs_dir` (e.g.
   `docs_dir/db-map.md`). State at the top that it is **descriptive and regenerable** — a snapshot of
   the schema, not a rule, and not the place for conventions. Change no schema and no source code.
