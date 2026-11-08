# Frontend track — measurable UI gates, composed taste

> **In 30 seconds.** `track: frontend` (or `fullstack`) adds UI gates that are measurable or greppable,
> scored against your project's `DESIGN.md`; taste stays yours. A universal UI requirement is proven on
> every reachable surface the code has. **Status:** Implemented in 1.21.0.

## The idea

`config.track` (`backend|frontend|fullstack`, default `backend`) selects the gate set, orthogonal to
TIER, so a ticket may be `track=frontend` + `TIER=lite`. `analysis` emits a counted `TRACK` artifact
the challenger can check. A `track=backend` ticket runs with none of the gates below.

**Own the durable, compose the volatile.** mango embeds only UI knowledge that is durable +
falsifiable — a11y thresholds it can *measure*, token-first it can *grep*, conformance to a
per-project **`DESIGN.md`** contract. It composes, never owns, the aesthetic layer: it calls an
external taste skill if installed, else follows `DESIGN.md`, and never stops because a taste skill is
missing. mango blocks on a missing *number*, never a missing aesthetic. Breakpoint values, the
narrow-width navigation pattern, and which regions collapse vs reflow are *choices* → they live in
`DESIGN.md`.

## How it works

- **`DESIGN.md` contract** (built by `design` from `templates/design-doc.md`): palette
  domain-meaning-first; a **shell** (character-rich) vs **data-core** (legibility-first, static) split;
  and a **Responsive & touch** section (breakpoints, narrow-width navigation, collapse vs reflow vs
  scroll, thumb-zone, motion).
- **Falsifiable rubric** (`templates/frontend-rubric.md`, injected into the reviewer/challenger
  brief): every item is measurable or greppable and scored **against `DESIGN.md`**; "is it tasteful?"
  is out of scope. Core items (token-first, no hardcoded hex/px, semantic HTML,
  state-not-by-colour-alone, `prefers-reduced-motion`) plus the **M1–M10** responsive/touch gates:

  | | Gate | Threshold |
  |---|------|-----------|
  | M1 | viewport meta / zoom not disabled | `width=device-width, initial-scale=1`; no `user-scalable=no` |
  | M2 | no horizontal page scroll at each breakpoint + 320 px floor | `scrollWidth ≤ clientWidth` |
  | M3 | reflow @320 px, no 2-D scroll | WCAG 1.4.10 |
  | M4 | touch-target size + spacing | ≥ 44×44 px (floor 24×24); ≥ 8 px apart |
  | M5 | input zoom guard | control `font-size ≥ 16px` |
  | M6 | tap/hover parity | nothing exposed only via `:hover` |
  | M7 | focus-visible + indicator contrast | ≥ 3:1 |
  | M8 | contrast | text ≥ 4.5:1; UI/state ≥ 3:1 |
  | M9 | safe-area respect | fixed/sticky edges use `env(safe-area-inset-*)` |
  | M10 | pointer-input parity | drag/resize/hover also fire via Pointer Events |

  Constants (44/24 px, 16 px, 4.5:1, 320 px) are **standards** → fixed, not config. M10 degrades
  gracefully: its greppable smell (a mouse/hover-only handler with no pointer equivalent) can block,
  but its runtime pointer-dispatch assert runs only when the environment can — otherwise it is a named
  coverage-gap exclusion and never wedges the gate.

## Surface coverage — the denominator comes from the code

For a universal / app-wide frontend requirement the failure usually hides on a reachable surface the
*ticket* never named. So `analysis` enumerates every reachable surface (route / overlay / modal /
major mounted state) from the **code** (the opt-in `sitemap` if present, else a read-only enumeration)
and emits a counted `SURFACES: N`; the ticket's examples are a hint, never the denominator.

`execute` records, per surface, the **highest available proof tier** in a **proof manifest**:
`PASS(automated)` (tier-1, satisfying the C1–C8 contract by composing the project's runner — mango
bundles none) → `PASS(render@<bp>)` (tier-2, a recorded render at the breakpoint asserting the visible
measurable — a first-class proof, not an exclusion) → `EXCLUDED` (human-approved, only when neither is
reachable). **e2e is optional, a proof is not**, and mango never stops for a missing runner. With `N`
surfaces, `M` proven (any tier), `X` exclusions, **Gate 2 passes iff `N == M + X`**; otherwise
`review` emits `⚠ surfaces proven: k/N` and blocks. Under `TIER=lite` the re-run lightens to
confirming proof presence — coverage stays mandatory.
