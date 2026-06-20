# PROJ-101 — Enforce password minimum length on all signup paths

**Constraint:** Must not change the existing hashing algorithm.

**Requirement:** Reject passwords shorter than 12 characters.

**Goal:** Every account-creation entry point validates length consistently.

**Acceptance Criteria:**
- A signup with an 11-character password is rejected with a clear error.
- A signup with a 12-character password succeeds.
- All signup paths (web form, API, admin-create) enforce the same rule.
