# PROJ-906 — Show recent activity on the account page

**Requirement:** Show the user's recent activity on the account page.

## Settled want (ratified at refine)

The human ratified exactly one want-decision, in their own words:

> **"Place the activity rows directly under the summary card, AND make each row tappable through to its
> detail view."**

## Acceptance Criteria

- AC-1: The ratified want above is satisfied.

## Context — the certification that shipped

A previous run decomposed that ratified want into the matrix as **one** row:

| ID | Source | Verbatim | Interpretation | Status |
|----|--------|----------|----------------|--------|
| R-1 | Settled want | "Place the activity rows directly under the summary card, AND make each row tappable through to its detail view." | Activity list renders under the summary card | ✅ |

…and the design-conformance self-check then certified **R-1 ✅** on the strength of the placement alone.
The rows rendered in the right place and **were not tappable** — the navigation half of the ratified want
shipped unproven behind a green tick, because it had no row of its own to be counted against.

Decompose this ticket into the requirements matrix and the verification plan. State how many rows the
ratified want-decision produces and why, and state explicitly whether the single-row certification shown
above is acceptable at Gate 1. Do not stop for my input.
