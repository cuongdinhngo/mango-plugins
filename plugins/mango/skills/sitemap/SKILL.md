---
name: sitemap
description: Opt-in, descriptive map of the code surface — routes/endpoints and modules — written into config.docs_dir. Generates regenerable facts (what the code IS), never normative rules. Stack-specific and off unless config.code_map_cmd (or a stack adapter) is set; not part of the lifecycle.
---

**`<mango>` = this plugin's root:** `${CLAUDE_PLUGIN_ROOT}` when the host sets it, else the plugin root
this skill file sits in, else a read-only search for a directory holding `PRINCIPLES.md` and
`.claude-plugin/plugin.json` — never a hardcoded path. Unresolvable → say so and use the inline fallback
named at the point of use (`<mango>/PRINCIPLES.md`, *Resolving a mango-shipped path*).

Operate under `<mango>/PRINCIPLES.md`. This skill is **descriptive only**: it generates
**facts** about the code surface (regenerable, falsifiable) — it never authors or infers a normative
rule. Normative conventions live in the `codify` rule book, not here.

**READ `<mango>/principles/descriptive-normative.md` NOW, before generating anything.** It is the binding
descriptive/normative boundary. Unconditional, not consult-if-relevant. If `<mango>` does not resolve, say
so and generate facts only — never a rule.

`sitemap` is **opt-in and stack-specific** — it is **not** part of the lifecycle and does nothing
unless configured. The lifecycle runs fully whether or not a sitemap has ever been generated.

## Steps

1. **Check configuration.** Read `${CLAUDE_PROJECT_DIR}/.harness.json`. The map needs either
   `config.code_map_cmd` (a project-supplied command that emits the route/module surface) or a stack
   adapter you can drive read-only. If neither is available, **report that `sitemap` is not configured**
   (name `config.code_map_cmd` and `config.docs_dir`) and **do nothing else** — no guessing.
2. **Generate the map (read-only).** Run `config.code_map_cmd` if set, else inspect the stack
   read-only, to produce a map of the **code surface**: routes / endpoints (method + path + handler)
   and modules / packages with their responsibilities. Delegate bulk read-and-extract to the Haiku
   `extractor` per `PRINCIPLES.md`.
3. **Write it to `config.docs_dir`.** Write a regenerable map file under `config.docs_dir` (e.g.
   `docs_dir/sitemap.md`). State at the top that it is **descriptive and regenerable** — a snapshot of
   what exists, not a rule. Change no source code.
