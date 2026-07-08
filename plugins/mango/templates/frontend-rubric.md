<!-- FRONTEND-RUBRIC TEMPLATE. The `review` skill injects this into the reviewer/challenger brief
ONLY when the track includes frontend. Every item is FALSIFIABLE — measurable or greppable — and is
scored AGAINST the project's DESIGN.md (config.design_doc_path), never against a blanket aesthetic
rule. "Is it tasteful?" is OUT of this rubric; taste exists only as DESIGN.md conformance. Do not
fork the reviewer agent per track — this is injected content, not a separate agent. -->

# Frontend rubric (scored against `DESIGN.md`)

Score every item below. Each is measurable or greppable; check it **against `config.design_doc_path`
(`DESIGN.md`)**, not against a generic rule. A blanket rule (e.g. "ban colour X") yields to the
domain meaning recorded in `DESIGN.md`.

## Core (always, when track includes frontend)

- **Matches `DESIGN.md`** — colour / font / spacing / radius come from the agreed tokens.
- **No hardcoded hex/px outside tokens** (grep the diff for raw `#rrggbb` / `NNpx` in component code).
- **Semantic HTML** — landmarks, headings, labelled controls; not `div` soup.
- **State never by colour alone** — every status carries an icon + text, not just a hue.
- **`prefers-reduced-motion` respected** — animation limited to `transform`/`opacity`, reduced/removed
  under the query.
- **No aesthetic change mixed into a logic/backend PR** — responsive/visual work rides its own branch.

## Responsive & touch — the M1–M10 gates (all falsifiable; each carries its risk layer for T2)

| ID | Gate (falsifiable) | Threshold · standard | Risk layer | Proof that clears Gate 2 |
|----|--------------------|----------------------|------------|--------------------------|
| M1 | viewport meta present; zoom not disabled | `width=device-width, initial-scale=1`; no `user-scalable=no`, no `maximum-scale<5` · WCAG 1.4.4 | document | static assert on served HTML |
| M2 | **page** has no horizontal scroll at each declared breakpoint **and** at the 320 px floor; a `data-core` region may scroll **inside its own bounded container** but the document must not | `scrollWidth ≤ clientWidth` on root + each top-level region | integration/runtime | automated-UI render at the widths, assert scrollWidth |
| M3 | reflow floor: content + function preserved at 320 px, no 2-D scroll | · WCAG 1.4.10 | integration/runtime | render @320 px, assert |
| M4 | touch-target size + spacing | ≥ 44×44 CSS px (absolute floor 24×24 · WCAG 2.5.8); ≥ 8 px between adjacent targets | computed-style | measure bounding boxes of interactive roles |
| M5 | input zoom guard | form controls computed `font-size ≥ 16px` | computed-style | `getComputedStyle` on input/textarea/select |
| M6 | tap/hover parity | no info or action exposed **only** via `:hover` | integration/runtime | render in no-hover/touch mode, assert reachable by tap+focus |
| M7 | focus-visible on every interactive element; indicator contrast ≥ 3:1 | · WCAG 2.4.7 / 2.4.11 | integration/runtime | tab traverse, assert indicator |
| M8 | contrast | text ≥ 4.5:1 (≥ 3:1 if ≥ 24 px or ≥ 19 px bold); UI/state ≥ 3:1 · WCAG 1.4.3 / 1.4.11 | computed-style | compute from resolved colours |
| M9 | safe-area respect | any fixed/sticky edge element references `env(safe-area-inset-*)` | integration/runtime | render with simulated insets, or static check |
| M10 | pointer-input parity | drag/resize/hover interactions also fire via touch (**Pointer Events**) | behavioral | two-part, degrades gracefully — see below |

Constants (44/24 px, 16 px, 4.5:1, 320 px) are **standards** → fixed rubric constants, not config.

## Multi-clause gates — one assertion PER CLAUSE (no proving the easy clause only)

Several gates carry a threshold with **more than one clause**. Each clause is proven **separately** —
the proof manifest carries **one row per clause**, and a clause with no assertion leaves the gate
**incomplete → it blocks, exactly as a missing surface does.** Asserting the easy clause (e.g. target
size) does **not** clear the gate while the other clause (e.g. spacing) is unproven. `execute`
enumerates the clauses named here — it does not invent new ones.

| Multi-clause gate | Clause 1 | Clause 2 |
|-------------------|----------|----------|
| M4 touch-target | `size` ≥ 44×44 px (floor 24×24) | `spacing` ≥ 8 px between adjacent targets |
| M7 focus-visible | indicator `visible` on every interactive element | indicator `contrast` ≥ 3:1 |

## Risk-layer floor (so the layer-match hard gate cannot be diluted)

`document`, `computed-style`, `integration/runtime`, and `behavioral` are **all ABOVE the
logic/unit layer.** A logic/unit-only proof (a mocked DOM) clears **none** of M1–M10.
`computed-style` requires a **real resolved DOM** (`getComputedStyle` on a rendered tree). The Gate-2
floor for these gates is "measured against a real rendered DOM (or the served document for M1)";
below that floor a row is `❌` or a recorded, human-approved coverage-gap exclusion. This reuses the
v0.6 layer-match mechanism — it does not fork it.

## M10 degrades gracefully (never wedges the review)

M10 has two parts:
1. **Always-on greppable smell** (always runs, can block): a mouse-only handler
   (`mousedown`/`mousemove`/`clientX`/`MouseEvent` with no pointer/touch equivalent) or a hover-only
   interaction. This part needs no special environment.
2. **Best-effort behavioral assert** (only when the environment can run it): dispatch a
   pointer/touch event and assert the handler fires. If the environment **cannot** run it, record the
   dispatch-assert as a **named, human-approved coverage-gap exclusion** — it does not block.

A non-runnable M10 behavioral assert **never blocks** the gate; the greppable smell still applies.
