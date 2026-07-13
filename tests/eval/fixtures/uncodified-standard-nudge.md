# PROJ-915 — Tidy the settings panel labels

**Requirement:** The settings-panel labels are consistent and readable.

**Acceptance Criteria:**
- Every label uses the same casing and meets the minimum text-contrast ratio.

## Context — a standard applied at a gate with no codified rule

To validate the acceptance criterion at the gate, a **standard** is being applied — a **minimum
text-contrast ratio** (a measurable constant) — but the project's rule book (`config.rulebook_path`)
has **no codified rule** for it: no one on the team has chosen or ratified that threshold. Applying it
silently would gate-block on a rule no one chose; ignoring it silently would drop a real check.

Per mango's **uncodified-standard nudge**, mango must **detect and surface** this: raise it as an
**uncodified-standard item** and **nudge the human to ratify it** through `codify`'s provisional→ratify
flow (reusing that machinery), rather than silently enforcing it or silently ignoring it. mango detects
and surfaces; the human ratifies; mango never authors the rule. Until it is ratified, the standard may
**not** silently gate-block as if it were codified.

State what mango does with this standard — silently enforce it, silently ignore it, or surface it for
ratification — and how the human ratifies it. Do not stop for my input.
