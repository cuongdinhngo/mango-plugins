# PROJ-715 — Add a "forgot password" flow

**Requirement:** Add a "forgot password" flow that emails a reset link.

## Context

A user who brings a raw requirement **cannot tell whether refine exposed too FEW decisions.** So refine
reuses the **ticket-blind challenger** as an **exposure-checker** — exactly **ONE dispatch** — asked
only *"is any product-decision still un-exposed?"* (e.g. the reset-link expiry window, single-use vs
reusable link, rate limiting) — **not** to argue answers.

This is the completeness-of-exposure backstop, achieved with **1 dispatch — NOT a multi-advisor
Council / debate**. Any decision the exposure-checker surfaces re-enters refine's loại-A / loại-B
classification. This fixture asserts the exposure-checker (ticket-blind challenger, 1 dispatch) runs and
can surface an un-exposed decision, and that it is not a multi-advisor debate.
