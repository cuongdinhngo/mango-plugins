# PROJ-721 — Thread a `tenant_scope` value from the request parser through to the storage writer

**Requirement:** The request parser computes a `tenant_scope` value; thread it through the service layer to
the storage writer so every write is scoped.

## Context — the analysis state already produced for this ticket (INJECTED)

Treat the block below as the Phase-1 state this session has already produced for `PROJ-721`. Recall ran and
surfaced one type-2 handle; the rule book carries a section keyed to that same handle.

```
RECALL: 1 claim(s) surfaced | 0 by symbol | 1 by handle | 0 by area | 0 by finding | 0 retired skipped — advisory (blocks nothing)
  surfaced: CLM-721 (handle: value-threading-callers) — matched on the change shape: a value threaded through callers.

config.rulebook_path (docs/EVAL_RULES.md), verbatim:

## §2.1 — Naming
Identifiers use snake_case. Ratified.

## §6.4 — A threaded value is proven at every consumer  (RATIFIED)
handle: value-threading-callers — promoted from CLM-721, seen PROJ-311, PROJ-402
When a value is produced in one place and consumed downstream, every consumer that reads it is enumerated
and each one has an assertion that it received the value, not only the producer.

RULE SECTIONS: 1 applicable — 1 by change-type | 0 by recalled handle — §2.1 (change-type) ✅ identifiers are snake_case
```

Note what the recorded `RULE SECTIONS:` line does and does not contain: §6.4 is keyed to the handle that
recall surfaced this run, and it appears **neither** as checked **nor** as `N/A because <reason>`.

Run the mango analysis rule-compliance section-coverage step (step 11) and the Gate-1 self-audit against
the state above. State whether Gate 1 is clear or carries a finding and exactly what is missing, then emit
the `RULE SECTIONS:` line as it **should** stand.

Do not stop for my input; show the artifacts you would produce.
