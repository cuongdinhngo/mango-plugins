# PROJ-718 — Add a soft-deletable `audit_note` table

**Requirement:** Add a new `audit_note` table (a DB migration/schema change) so operators can attach
notes to records. Notes must be soft-deletable and readable by the reporting role.

## Context

This change-list includes a **migration / schema change**, so analysis's rule-compliance step must
**enumerate the rulebook sections applicable to THIS change type** and check each one — not an ad-hoc
subset. Because the change type is a migration, the **DB-conventions section is mandatory**: it covers
grants/permissions (a migration that ships without the section's GRANT breaks in prod with
permission-denied), soft-delete, naming, and indexing.

The applicable-section list is **derived from the change type**, and each applicable section is
explicitly checked (or marked N/A with a reason) and emitted as the counted `RULE SECTIONS` artifact.

This fixture exercises rule-compliance section coverage: a change-list containing a migration →
analysis **enumerates the DB-conventions section and checks grants/soft-delete**; **omitting an
applicable section is a finding** (non-vacuous — silently dropping the DB-conventions section on a
migration is exactly the production-breaker this removes).
