<!-- DESIGN-DOC TEMPLATE. On the frontend track, `design` copies this to `config.design_doc_path`
(default DESIGN.md at the repo root) and fills it for the project, then keeps it updated. It is the
per-project DESIGN CONTRACT: the frontend review rubric is scored AGAINST this file, never against a
blanket rule baked into mango. Everything here is a project CHOICE — breakpoint values, the
narrow-width navigation pattern, which regions collapse vs reflow, thumb-zone priority, motion — so
it lives here, not in the plugin. mango blocks on a missing NUMBER (a threshold it can measure), never
on a missing aesthetic. Aesthetic GENERATION belongs to an external taste skill if one is installed;
if none is, follow this file — never stop because a taste skill is absent. -->

# DESIGN.md — the project design contract

## Tokens (the single source of truth)

All colour, spacing, radius, and typography flow through **named design tokens** (theme + CSS custom
properties). No scattered hardcoded hex/px in components — the review rubric greps for them.

### Palette — domain meaning FIRST, general rules SECOND

Derive colours from what they **mean in this domain** before applying any general aesthetic rule. A
blanket rule ("never use colour X") must yield to domain meaning — a domain term may literally denote
that colour, or a status colour may be fixed by convention/regulation. Record the meaning beside each
token so the reviewer checks against this contract, not a generic ban.

| Token | Value | Domain meaning / where used |
|-------|-------|-----------------------------|
| `--color-...` |  |  |

State is **never conveyed by colour alone** — every status carries an icon + text label as well.

### Typography / spacing / radius

| Token | Value | Used for |
|-------|-------|----------|
| `--font-...` |  |  |
| `--space-...` |  |  |
| `--radius-...` |  |  |

## Surface split — shell vs data-core

Separate the two surface kinds; they have different design goals.

- **Shell** — character-rich pages (landing, marketing, navigation chrome, empty states). Expression
  and brand live here.
- **Data-core** — tables, grids, dense forms, charts. **Legibility-first and static**: restrained
  motion, high contrast, predictable layout. A `data-core` region may scroll **inside its own bounded
  container**, but the document itself must not (see M2).

For each, note the components it covers and any rules specific to it:

| Surface | Components | Rules |
|---------|-----------|-------|
| shell |  |  |
| data-core |  |  |

## Responsive & touch (the choices the M1–M10 gates are scored against)

These are project decisions. The gates measure conformance to them; they do not dictate them.

- **Declared breakpoints:** <widths, e.g. 375 / 768 / 1280 — mirror `config.breakpoints`>. The 320 px
  reflow floor is a standard, always tested.
- **Narrow-width navigation pattern:** <e.g. collapse the primary nav into a disclosure menu;
  bottom tab bar; off-canvas drawer — pick one and describe the trigger>.
- **Region behaviour at narrow widths — collapse vs reflow vs scroll-in-container:** for each major
  region, state which it does. (The page must never scroll horizontally; a data-core region may
  scroll inside its own bounded container.)

  | Region | collapse / reflow / scroll-in-container |
  |--------|------------------------------------------|
  |        |                                          |

- **Thumb-zone priority:** which primary actions must sit within easy thumb reach on a held phone.
- **Motion policy:** what animates and how. Honour `prefers-reduced-motion`; limit animation to
  `transform`/`opacity`. Note any motion the data-core surface forbids.

## Interaction

- Interactions use **Pointer Events**, not mouse-only handlers. No information or action is exposed
  **solely** via `:hover` (it must also be reachable by tap + focus).
- Every interactive element has a visible **focus indicator** (see M7).
