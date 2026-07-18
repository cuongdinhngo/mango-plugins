# PROJ-820 — Build the internal analytics portal

**Requirement:** Build a new internal analytics portal: team sign-in, a metrics dashboard, a saved-view
manager, and an export centre.

## Context

This input is an **EPIC**, not a single ticket — the exposed work spans multiple independent,
each-execute-able deliverables (sign-in, dashboard, saved-views, export). refine detects the epic and
routes to the **epic path** (analysis(epic) → design(epic) → breakdown → N× ticket-lifecycles).

The **completeness-of-exposure backstop is NOT exempt on the epic path.** Before `breakdown`, refine
dispatches the **SAME 1-dispatch ticket-blind exposure-checker** the ticket path uses — exactly one
dispatch, not a multi-advisor debate — over the epic's exposed set, asking only "is any product-decision
still un-exposed?". Its findings surface for the human to ratify alongside the breakdown. An un-exposed
decision is *most* costly at epic scale, so the epic is the one path that must never skip the backstop.

For example, an un-exposed product-decision here — "who counts as an internal user (SSO group? any
employee? contractors?)" — is exactly the kind of thing the exposure-checker can surface before the
epic is split into tickets, non-vacuously.
