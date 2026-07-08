# PROJ-602 — Rename the dashboard heading copy

**Requirement:** The dashboard page heading must read "Activity overview" instead of the current
"Recent activity".

**Goal:** Ship the copy change without leaving a stale assertion that still expects the old heading.

**Acceptance Criteria:**
- The dashboard renders the heading text "Activity overview".

## Existing tests in the repo (blast radius)

An existing shell/spec test asserts the old heading:

```
tests/dashboard_heading_spec.sh:  assert_contains "$html" "Recent activity"
```

Changing the heading copy invalidates that assertion — the test still expects "Recent activity".
