# PROJ-722 — Rename an internal helper in the report renderer

**Requirement:** Rename the file-local helper `fmt_row` to `format_row` in the report renderer. No caller
outside that file, no exported symbol, no schema, no UI surface.

## Context — the analysis state already produced for this ticket (INJECTED)

Treat the block below as the Phase-1 state this session has already produced for `PROJ-722`.

```
RECALL: 1 claim(s) surfaced | 0 by symbol | 1 by handle | 0 by area | 0 by finding | 0 retired skipped — advisory (blocks nothing)
  surfaced: CLM-722 (handle: shared-vocabulary-rename) — surfaced advisorily on the rename shape.

config.rulebook_path (docs/EVAL_RULES.md), verbatim:

## §2.1 — Naming
Identifiers use snake_case. Ratified.

## §7.1 — A shared vocabulary rename updates every consumer in the same change  (RATIFIED)
handle: shared-vocabulary-rename — promoted from CLM-722, seen PROJ-140, PROJ-208
When a shared/generated type, enum, or exported symbol is renamed, every consumer is updated in the same
change and the enumeration command and its output are recorded.

RULE SECTIONS: 2 applicable — 1 by change-type | 1 by recalled handle — §2.1 (change-type) ✅ the new name `format_row` is snake_case · §7.1 (recalled handle) N/A because the helper is file-local and not exported: `grep -rn "fmt_row" .` returns only the one file, so there is no consumer to update
```

Run the mango analysis rule-compliance section-coverage step (step 11) and the Gate-1 self-audit against
the state above. State whether the recorded answer to the handle-matched section §7.1 is a **legal** answer,
whether Gate 1 is clear or blocked, and emit the `RULE SECTIONS:` counting line. Then say whether the
handle-matched source made this ticket carry any extra investigation beyond the one line it was answered
with.

Do not stop for my input; show the artifacts you would produce.
