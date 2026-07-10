# PROJ-742 — Null-guard the shared config loader

**Requirement:** `loadConfig()` in the shared config module must return an empty object instead of
throwing when the config file is absent.

**Acceptance Criteria:**
- `loadConfig()` returns `{}` when the file does not exist; behaviour is unchanged when it does.

## Context (as submitted for execute)

This change edits **one function** (`loadConfig`) in a **shared, pre-existing** module,
`config_loader`. That same file holds many other functions whose pre-existing formatting the
project's formatter would rewrite. Running the project's formatter over the **whole file** would
reformat dozens of **untouched** lines outside this change; a separate shared utility file is also
present in the diff's directory and is likewise formattable.
