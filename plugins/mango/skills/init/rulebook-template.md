# Engineering Guide

> Starter rule book scaffolded by `/mango:init`. Sections pre-filled from **observed** codebase
> patterns only; every `TODO` is a decision the team must make. mango's `reviewer`/`challenger`
> ground their findings in this file on every run — keep it the single source of truth. (You may
> later split this into a directory of `*.md` files and point `rulebook_path` at the folder.)

## Contents
- [Architecture](#architecture)
- [Coding standards / Conventions](#coding-standards--conventions)
- [Security (must / never)](#security-must--never)
- [Data access](#data-access)
- [Error handling](#error-handling)
- [Testing & the Definition of Done](#testing--the-definition-of-done)

## Architecture
<!-- Observed: layout, entry points, module boundaries. -->
- TODO: describe the high-level architecture and where logic belongs (layers/modules).
- TODO: what may depend on what; forbidden dependencies.

## Coding standards / Conventions
<!-- Observed: language(s), formatter/linter config, naming patterns. -->
- TODO: formatting/linting command and when it must pass.
- TODO: naming conventions and file organisation rules.

## Security (must / never)
- TODO: how untrusted input must be validated/sanitised before reaching a sink.
- TODO: authn/authz expectations for new endpoints.
- NEVER: hardcode secrets; secrets live in a gitignored `.env`.

## Data access
- TODO: the approved data-access pattern (parameterised queries / ORM usage).
- TODO: the migration workflow; schema changes must go through it.

## Error handling
- TODO: how errors are surfaced, logged, and wrapped.
- TODO: transaction/rollback expectations for multi-step writes.

## Testing & the Definition of Done
<!-- Observed: test runner / command. -->
- TODO: what level of test is required for a change (the proving test mango asks for).
- TODO: the Definition of Done checklist for a ticket.
